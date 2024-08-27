poetry를 사용해 패키지 관리하기 (feat. pip)
============================


📍 Python pip를 사용하지 않아보려 한다.
----------------------------

pip는 Python용 패키지 설치 프로그램이다. 이를 사용해 여러 Python 패키지를 설치 할 수 있다.

pip를 계속해서 사용하면 가장 불편한 점은 패키지를 설치하면 전역적으로 설치가 된다는 점과 자신이 어떤 패키지를 설치했는지 확인하기 위해 `$ pip list`, `$ pip freeze` 명령어를 입력하면 "설치한 패키지 + 해당 패키지에 필요한 패키지(=의존된 패키지)"들이 나오게 된다. `$ pip freeze > requirements.txt` 명령어를 통해 requirements.txt 파일을 만들 때는 더 짜증났다.

이러한 불편한 점을 해결하기 위해 가상환경을 새롭게 만들고 해당 환경에서 필요한 패키지를 설치했고, 나중에 쉽게 이해할 수 있게 requirements.txt 파일에는 내가 설치한 패키지들을 수동으로 넣어줬다.

이러한 작업이 익숙해진 시점에 [poetry](https://python-poetry.org/docs/)라는 Python에서 종속성 관리 및 패키징을 위한 도구를 알게 됐고 사용해보려고 한다.

📍 Poetry 란
-----------

> Poetry is a tool for **dependency management** and **packaging** in Python.

Python 프로젝트의 의존성를 선언, 관리, 설치하여 어디서나 프로젝트가 작동하도록 도와주는 툴이다.
pip와는 다르게 `.toml` , `.lock` 파일을 생성해 **의존성를 관리**한다.

*   `.toml`: 프로젝트 의존성의 메타 데이터 저장
    *   프로젝트와 의존성들 간의 충돌을 해결해준다.
*   `.lock`: 설치된 패키지들의 version, hash 저장
    *   해당 파일을 사용해 프로젝트 의존성을 다른 환경에서도 동일하게 유지할 수 있도록 도와준다.

📍Poetry 설치
-----------

*   설치 명령어

    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

    # 실행 후 설치 완료 메시지
    ...
    Poetry (1.1.13) is installed now. Great!

    To get started you need Poetry's bin directory ($HOME/.poetry/bin) in your `PATH`
    environment variable. Next time you log in this will be done
    automatically.

    To configure your current shell run `source $HOME/.poetry/env`

*   설치 완료 후 설정 해주기 위해 해당 명령어 입력

    source $HOME/.poetry/env

*   제대로 설정 됐는지 확인

    # 파일 오픈
    open ~/.zshrc

    # 맨 마지막 줄에 해당 부분이 있는지 확인
    export PATH="$HOME/.poetry/bin:$PATH"

*   `.poetry` 폴더 생성 됐는지 확인

    ls -al
    >> .poetry

*   버전 확인

    poetry --version
    >> Poetry version 1.1.13

📍 Poetry init
--------------

*   초기 실행 명령어

    poetry init

    # 우선 모두 Enter를 눌러 기본값이 어떻게 설정되는지 확인

    This command will guide you through creating your pyproject.toml config.

    Package name [poetry-test]:
    Version [0.1.0]:
    Description []:
    Author [Choi Insu <insutance@naver.com>, n to skip]:
    License []:
    Compatible Python versions [^3.9]:

    Would you like to define your main dependencies interactively? (yes/no) [yes]
    You can specify a package in the following forms:
      - A single name (requests)
      - A name and a constraint (requests@^2.23.0)
      - A git url (git+https://github.com/python-poetry/poetry.git)
      - A git url with a revision (git+https://github.com/python-poetry/poetry.git#develop)
      - A file path (../my-package/my-package.whl)
      - A directory (../my-package/)
      - A url (https://example.com/packages/my-package-0.1.0.tar.gz)

    Search for package to add (or leave blank to continue):

    Would you like to define your development dependencies interactively? (yes/no) [yes]
    Search for package to add (or leave blank to continue):

    Generated file

    [tool.poetry]
    name = "poetry-test"
    version = "0.1.0"
    description = ""
    authors = ["Choi <insutance@naver.com>"]

    [tool.poetry.dependencies]
    python = "^3.9"

    [tool.poetry.dev-dependencies]

    [build-system]
    requires = ["poetry-core>=1.0.0"]
    build-backend = "poetry.core.masonry.api"

    Do you confirm generation? (yes/no) [yes]

*   init을 하고나면 `pyproject.toml` 파일이 생성된 것을 확인할 수 있다.

    [tool.poetry]
    name = "poetry-test"
    version = "0.1.0"
    description = ""
    authors = ["Choi <insutance@naver.com>"]

    [tool.poetry.dependencies]
    python = "^3.9"

    [tool.poetry.dev-dependencies]

    [build-system]
    requires = ["poetry-core>=1.0.0"]
    build-backend = "poetry.core.masonry.api"

> 다시 `$ poetry init` 명령어를 입력하니 아래와 같은 에러 메시지 출력됨.

    A pyproject.toml file with a poetry section already exists.

📍Poetry Python Version Test
----------------------------

`$ poetry init` 명령어를 실행할 때 여러 입력값 넣는 부분을 엔터를 통해 넘어갔다.
잠깐 자세히 보면 Python Version이 **자동으로** 들어간 것을 확인할 수 있다.

*   `Compatible Python versions [^3.9]:`

어떻게 자동으로 Python Version이 들어가며, 자동으로 설정되는 버전의 기준이 뭘까?
결론부터 말하자면, **Poetry는 현재 설치 또는 설정된 Python Version으로 자동으로 설정**된다.

### pyenv를 사용해 2가지 버전 설치

    pyenv install 3.10.2
    pyenv install 3.9.11

### Python Version 3.10

3.10.2 버전으로 설정

    pyenv local 3.10.2

poetry init 실행 후 생성된 `pyproject.toml` 파일 내용

    [tool.poetry]
    name = "poetry-test"
    version = "0.1.0"
    description = ""
    authors = ["Choi <insutance@naver.com>"]

    [tool.poetry.dependencies]
    python = "^3.10"  # Python Version 3.10

    [tool.poetry.dev-dependencies]

    [build-system]
    requires = ["poetry-core>=1.0.0"]
    build-backend = "poetry.core.masonry.api"

### Python Version 3.9

3.9.11 버전으로 설정

    pyenv local 3.9.11

poetry init 실행 후 생성된 `pyproject.toml` 파일 내용

    [tool.poetry]
    name = "poetry-test"
    version = "0.1.0"
    description = ""
    authors = ["Choi <insutance@naver.com>"]

    [tool.poetry.dependencies]
    python = "^3.9"  # Python Version 3.9

    [tool.poetry.dev-dependencies]

    [build-system]
    requires = ["poetry-core>=1.0.0"]
    build-backend = "poetry.core.masonry.api"

📍 패키지 설치 및 삭제
--------------

*   [command link](https://python-poetry.org/docs/cli)

    # 패키지 설치
    $ poetry add {PACKAGE}

    # 패키지 삭제
    $ poetry remove {PACKAGE}

처음 패키지 설치를 하게 되면 poetry는 **자동으로 가상환경을 생성**하는 것을 볼 수 있다.
`${HOME}/Library/Caches/pypoetry/virutalenvs/{PROJECT-NAME}-{HASH}` 형태로 가상환경이 생성.

    $ poetry add pytest
    >> Creating virtualenv test-poetry-q0_x2Fq6-py3.9 in /Users/insutance/Library/Caches/pypoetry/virtualenvs
    ...

`pyproject.toml` 파일을 보게 되면 자신이 **설치한 패키지가 무엇인지 명확하게 볼 수 있다**.

    [tool.poetry]
    name = "test-poetry"
    version = "0.1.0"
    description = ""
    authors = ["Choi <insutance@naver.com>"]

    [tool.poetry.dependencies]
    python = "^3.9"
    pytest = "^7.1.2" # pytest를 설치했다는 것을 바로 알 수 있음.

    [tool.poetry.dev-dependencies]

    [build-system]
    requires = ["poetry-core>=1.0.0"]
    build-backend = "poetry.core.masonry.api"

똑같이 pyenv virtualenv를 사용해서 가상환경을 생성한 후, pytest 패키지를 설치해본 결과는 이처럼 내가 설치한 패키지가 무엇인지 기억하지 않는 이상 명확하게 볼 수 없다.

    # pytest 설치 전

    $ pip list
    Package    Version
    ---------- -------
    pip        22.1.2
    setuptools 58.1.0

    # pytest 설치 후

    $ pip list
    Package    Version
    ---------- -------
    attrs      21.4.0
    iniconfig  1.1.1
    packaging  21.3
    pip        22.1.2
    pluggy     1.0.0
    py         1.11.0
    pyparsing  3.0.9
    pytest     7.1.2
    setuptools 58.1.0
    tomli      2.0.1

    $ pip freeze
    attrs==21.4.0
    iniconfig==1.1.1
    packaging==21.3
    pluggy==1.0.0
    py==1.11.0
    pyparsing==3.0.9
    pytest==7.1.2
    tomli==2.0.1

📍 poetry install
-----------------

[install 명령](https://python-poetry.org/docs/cli#install)은 현재 프로젝트에서 `pyproject.toml` 파일을 읽고 종속성을 해결하고 설치.

    poetry install

📍마무리
-----

이처럼 간단하게 poetry를 사용해보면서 pip에서 느꼈던 불편함을 해소할 수 있었다.
많은 기능들이 있기 때문에 문서를 보면서 자신이 원하는 기능을 사용하면 될 것 같다:)