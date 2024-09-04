import typer
import requests
import json
import os
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


def check_path(
    input: str, output: str = None, remind: str = None
) -> tuple[str, str, str]:
    input = path.abspath(input)

    t = dt.now().strftime("%y%m%d_%H%M%S")

    if output is None:
        output = (
            path.splitext(input)[0].replace(" ", "_")
            + "_output_"
            + t
            + path.splitext(input)[1]
        )

        remind = (
            path.splitext(input)[0].replace(" ", "_")
            + "_remind_"
            + t
            + path.splitext(input)[1]
        )

    typer.echo("입력파일: %s" % input)
    typer.echo("출력파일: %s" % output)

    if not path.exists(input):
        err = FileNotFoundError(
            "[FileNotFoundError] 입력 파일이 존재하지 않습니다. (%s)" % input
        )
        raise err

    return input, output, remind


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


def geocode_process(
    df: DataFrame, addr: str, key: str, input: str, output: str, remind: str
) -> DataFrame:
    data: DataFrame = df.copy()
    size: int = len(data)
    success = 0
    fail = 0

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
                        fail += 1
                    except ValueError as ve:
                        # typer.echo(ve)
                        logger.warning(ve)
                        data.loc[i, "latitude"] = None
                        data.loc[i, "longitude"] = None
                        fail += 1
                    except Exception as e:
                        fail += 1
                        executor.shutdown(wait=False, cancel_futures=True)

                        if i > 0:
                            data.iloc[:i].to_excel(output, index=False)
                            # data.iloc[i:].to_excel(remind, index=False)
                            os.remove(input)
                            data.iloc[i:].to_excel(input, index=False)

                        raise e
                    finally:
                        pbar.set_postfix({"success": success, "fail": fail})
                        pbar.update(1)

    data["latitude"] = data["latitude"].astype(float)
    data["longitude"] = data["longitude"].astype(float)
    data.to_excel(output, index=False)
    typer.echo("------------------------------------------")
    typer.echo(f"총 {size}개의 데이터 중 {success}개의 데이터가 처리되었습니다.")
    typer.echo("------------------------------------------")

    return data


@app.command()
def main(
    key: str = typer.Option(),
    input: str = typer.Option(),
    output: str = None,
    addr: str = "address",
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
        input, output, remind = check_path(input=input, output=output)
        df: DataFrame = get_dataframe(input=input, addr=addr)
        geocode_process(
            df=df, addr=addr, key=key, input=input, output=output, remind=remind
        )
    except Exception as e:
        logger.error(e)
        typer.echo("------------------------------------------")
        typer.echo(e)
        typer.echo("------------------------------------------")


if __name__ == "__main__":
    app()
