import typer
import requests
import json
import concurrent.futures as futures
from os import path
from datetime import datetime as dt
from pandas import read_excel, read_csv, DataFrame
from tqdm import tqdm
import time

app = typer.Typer()


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
        raise FileNotFoundError("입력 파일이 존재하지 않습니다.")

    return input, output


def get_dataframe(input: str, addr: str) -> DataFrame:
    extname: str = path.splitext(input)[1].lower()

    if extname == ".csv":
        df: DataFrame = read_csv(filepath_or_buffer=input, encoding="utf-8")
    elif extname == ".xlsx":
        df: DataFrame = read_excel(io=input)
    else:
        raise ValueError("지원하지 않는 파일 형식입니다.")

    typer.echo("주소필드: %s" % addr)

    if addr not in df.columns:
        raise ValueError("입력파일에 주소필드가 존재하지 않습니다.")

    return df


def geocode_item(index: int, addr: str, key: str) -> dict:
    time.sleep(0.5)

    if not addr:
        errMsg = "주소가 존재하지 않습니다."
        raise ValueError(errMsg)
        # typer.echo(errMsg)
        # return None, errMsg, index, addr

    url: str = (
        f"https://api.vworld.kr/req/address?service=address&request=getCoord&key={key}&address={addr}&type=ROAD&format=json"
    )
    typer.echo(url)
    response: requests.Response = requests.get(url)

    if response.status_code != 200:
        errMsg = f"[{index}] {addr} >>> API 요청에 실패했습니다."
        raise Exception(errMsg)
        # return None, errMsg, index, addr

    response.encoding = "utf-8"
    result = response.json()

    status = result["response"]["status"]

    if status == "ERROR":
        error_code = result["response"]["error"]["code"]
        error_text = result["response"]["error"]["text"]

        errMsg = f"[{index}] {addr} >>> [{error_code}] {error_text}"
        raise Exception(errMsg)
        # typer.echo(errMsg)
        # return None, errMsg, index, addr
    elif status == "NOT_FOUND":
        errMsg = f"[{index}] {addr} >>> 주소를 찾을 수 없습니다."
        raise Exception(errMsg)
        # typer.echo(errMsg)
        # return None, errMsg, index, addr

    longitude = result["response"]["result"]["point"]["x"]
    latitude = result["response"]["result"]["point"]["y"]
    result: tuple[int, Any, Any] = (index, latitude, longitude)
    # print(result)
    return result, index, addr


def geocode_process(df: DataFrame, addr: str, key: str) -> DataFrame:
    data: DataFrame = df.copy()
    size: int = len(data)
    success = 0
    processes = []

    typer.echo("------------------------------------------")

    with open("geocoder.log", "w", encoding="utf-8") as f:
        with tqdm(total=size, colour="yellow") as pbar:
            with futures.ThreadPoolExecutor(max_workers=10) as executor:
                for i in range(size):
                    address: str = str(data.loc[i, addr]).strip()

                    if address == "nan":
                        pbar.update(1)
                        continue

                    processes.append(
                        executor.submit(geocode_item, index=i, addr=address, key=key)
                    )

                for p in futures.as_completed(processes):
                    try:
                        result, index, addr = p.result()
                    except Exception as exc:
                        typer.echo(exc)
                        f.write(str(exc))
                        f.write("\n")

                        if str(exc).find("LIMIT") > -1:
                            executor.shutdown(wait=True, cancel_futures=True)
                    else:
                        index, latitude, longitude = result
                        data.loc[index, "latitude"] = latitude
                        data.loc[index, "longitude"] = longitude
                        f.write(f"[{index}] {addr} >> {latitude}, {longitude}")
                        pbar.update(1)
                        success += 1

    data["latitude"] = data["latitude"].astype(float)
    data["longitude"] = data["longitude"].astype(float)

    typer.echo("------------------------------------------")
    typer.echo(
        f"총 {size}개의 데이터 중 {success}개의 데이터가 성공적으로 처리되었습니다."
    )

    return data


@app.command()
def main(
    key: str = typer.Option(),
    input: str = typer.Option(),
    output: str = None,
    addr: str = "ADDR",
) -> None:
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
    input, output = check_path(input=input, output=output)
    df: DataFrame = get_dataframe(input=input, addr=addr)
    result: DataFrame = geocode_process(df=df, addr=addr, key=key)

    result.to_excel(output, index=False)


if __name__ == "__main__":
    app()
