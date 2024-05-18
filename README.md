# py-geocoder 


![Badge](https://img.shields.io/badge/Author-Lee%20KwangHo-blue.svg?style=flat-square&logo=appveyor) &nbsp;
![Badge](https://img.shields.io/badge/Author-Ju%20YoungA-pink.svg?style=flat-square&logo=appveyor) &nbsp;
![Generic badge](https://img.shields.io/badge/version-0.1.0-critical.svg?style=flat-square&logo=appveyor) &nbsp;
[![The MIT License](https://img.shields.io/badge/license-MIT-orange.svg?style=flat-square&logo=appveyor)](http://opensource.org/licenses/MIT) &nbsp;
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=appveyor) &nbsp;
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=appveyor) &nbsp;

이 자료는 연세대학교 도시공학과 주영아(j.purplerose@gmail.com)의 논문 프로젝트에 활용되기 위해 작성된 Geocoder 툴 입니다.

## Installation

`pip` 명령으로 `*.whl` 파일을 설치합니다.

### [1] Remote Repository

```shell
pip install --upgrade https://raw.githubusercontent.com/leekh4232/py-geocoder/main/dist/py_geocoder-0.1.0-py3-none-any.whl
```


## Uninstallation

```shell
pip uninstall -y py-geocoder
```


## Useage

터미널에서 다음의 명령을 수행합니다.

```shell
$ py-geocoder --key={브이월드OpenAPI키} --input=주소가작성된엑셀,CSV파일경로 --addr=주소필드이름
```
