import typer
import requests
import json
import concurrent.futures as futures
from os import path
from datetime import datetime as dt
from pandas import read_excel, read_csv, DataFrame
from tqdm import tqdm
import time
import logging as logger

app = typer.Typer()


logfileName = dt.now().strftime("py-geocoder-%Y%m%d-%H.log")

logger.basicConfig(
    filename=logfileName,
    level=logger.INFO,
    encoding="utf-8",
    format="%(asctime)s %(levelname)s:%(message)s",
    filemode="a",
    datefmt="[%m/%d/%Y %I:%M:%S %p]",
)


def check_path(input: str, output: str = None) -> tuple[str, str, str]:
    input = path.abspath(input)

    if output is None:
        output = (
            path.splitext(input)[0].replace(" ", "_")
            + "_geocoded"
            + path.splitext(input)[1]
        )

    typer.echo("입력파일: %s" % input)
    typer.echo("출력파일: %s" % output)

    if not path.exists(input):
        err = FileNotFoundError(
            "[FileNotFoundError] 입력 파일이 존재하지 않습니다. (%s)" % input
        )
        raise err

    return input, output


def get_dataframe(input: str, addr: str) -> DataFrame:
    extname: str = path.splitext(input)[1].lower()

    if extname == ".csv":
        df: DataFrame = read_csv(filepath_or_buffer=input, encoding="utf-8")
    elif extname == ".xlsx":
        df: DataFrame = read_excel(io=input)
    else:
        raise ValueError("[ValueError] 지원하지 않는 파일 형식입니다.")

    typer.echo("주소필드: %s" % addr)

    if addr not in df.columns:
        raise ValueError("[ValueError] 입력파일에 주소필드가 존재하지 않습니다.")

    return df


def geocode_item(session, index: int, addr: str, key: str) -> dict:
    if not addr or addr == "nan":
        raise ValueError(
            "[Warning] 주소가 존재하지 않습니다. (%d) -> %s" % (index, addr)
        )

    url: str = f"https://api.vworld.kr/req/address"
    params = {
        "service": "address",
        "request": "getCoord",
        "key": key,
        "address": addr,
        "type": "ROAD",
        "format": "json",
    }

    response = None

    try:
        response = session.get(url, params=params, timeout=(3, 30))
    except Exception as e:
        raise e

    if response.status_code != 200:
        raise Exception(
            "[%d-Error] %s - API 요청에 실패했습니다. (%d) -> %s"
            % (response.status_code, response.reason, index, addr)
        )

    response.encoding = "utf-8"
    result = response.json()
    status = result["response"]["status"]

    if status == "ERROR":
        error_code = result["response"]["error"]["code"]
        error_text = result["response"]["error"]["text"]
        raise Exception(f"[{error_code}] {error_text} (%d) -> %s" % (index, addr))
    elif status == "NOT_FOUND":
        raise requests.exceptions.RequestException(
            "[Warning] 주소를 찾을 수 없습니다. (%d) -> %s" % (index, addr)
        )

    longitude = float(result["response"]["result"]["point"]["x"])
    latitude = float(result["response"]["result"]["point"]["y"])
    result = (latitude, longitude)
    logger.info("%s --> (%s, %s)" % (addr, latitude, longitude))
    return result


def geocode_process(df: DataFrame, addr: str, key: str) -> DataFrame:
    data: DataFrame = df.copy()
    size: int = len(data)
    success = 0

    typer.echo("요청 데이터 개수: %d" % size)

    typer.echo("------------------------------------------")

    with tqdm(total=size, colour="yellow") as pbar:
        with requests.Session() as session:
            with futures.ThreadPoolExecutor(max_workers=30) as executor:
                for i in range(size):
                    time.sleep(0.1)
                    address: str = str(data.loc[i, addr]).strip()

                    p = executor.submit(
                        geocode_item, session, index=i, addr=address, key=key
                    )

                    try:
                        result = p.result()
                        latitude, longitude = result
                        data.loc[i, "latitude"] = latitude
                        data.loc[i, "longitude"] = longitude
                        success += 1
                    except requests.exceptions.RequestException as re:
                        # typer.echo(re)
                        logger.warning(re)
                        data.loc[i, "latitude"] = None
                        data.loc[i, "longitude"] = None
                    except ValueError as ve:
                        # typer.echo(ve)
                        logger.warning(ve)
                        data.loc[i, "latitude"] = None
                        data.loc[i, "longitude"] = None
                    except Exception as e:
                        executor.shutdown(wait=False, cancel_futures=True)

                        if i > 0:
                            t = dt.now().strftime("%y%m%d_%H%M%S")
                            data.iloc[:i].to_excel("finish_%s.xlsx" % t, index=False)
                            data.iloc[i:].to_excel("remind_%s.xlsx" % t, index=False)

                        raise e
                    finally:
                        pbar.update(1)

    typer.echo("------------------------------------------")

    data["latitude"] = data["latitude"].astype(float)
    data["longitude"] = data["longitude"].astype(float)

    typer.echo("------------------------------------------")
    typer.echo(
        f"총 {size}개의 데이터 중 {success}개의 데이터가 성공적으로 처리되었습니다."
    )

    return data


@app.command()
def main(
    # key: str = "25DE1852-F870-357A-AF47-169CE76AA841", # 2020
    # key: str = "E0B70A87-4BB5-3081-8CC8-23B42575DB15",  # 2019
    # key: str = "ABD3E6CE-9D11-3C9A-8E58-9D3A3499D1EF", # 2018
    key: str = "9D94A39E-E3D6-3C84-9661-0F461B04BCDD",  # 2021
    input: str = typer.Option(),
    output: str = None,
    addr: str = "도로명",
) -> None:
    # def main(key: str = typer.Option(), input: str = typer.Option(), output: str = None, addr: str = 'ADDR') -> None:
    """
    -----------\n
    브이월드 OpenAPI와 연동하여 GeoCoding을 수행하고 결과를 파일로 저장합니다.\n \n
    -----------\n
    Args:\n
        - key (str): 브이월드에서 발급받은 API KEY\n
        - input (str): 데이터 파일의 경로 (Excel or UTF-8 CSV)\n
        - output (str, optional): 결과 파일의 경로. Defaults to None.\n
        - addr (str, optional): 주소 필드 이름. Defaults to 'ADDR'.\n
    -----------\n
    """

    try:
        input, output = check_path(input=input, output=output)
        df: DataFrame = get_dataframe(input=input, addr=addr)
        result: DataFrame = geocode_process(df=df, addr=addr, key=key)
        result.to_excel(output, index=False)
    except Exception as e:
        logger.error(e)
        typer.echo(e)


if __name__ == "__main__":
    app()
