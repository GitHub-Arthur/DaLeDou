import re
from shutil import copy
from importlib import reload
from os import environ, path, getenv

import yaml
import requests
from loguru import logger

import settings
from src.pushplus import pushplus
from src.daledou.daledouone import DaLeDouOne
from src.daledou.daledoutwo import DaLeDouTwo


_YAML_PATH = './config'


def _error(cookie: str):
    if 'uin' in cookie:
        msg = _search(r'uin=o(\d+)', cookie)
    else:
        msg = cookie
    logger.error(f'无效cookie：{msg}')
    pushplus(f'无效cookie {msg}', [f'{msg}无效'])


def _search(mode: str, html: str) -> str | None:
    '''
    返回第一个成功匹配的字符串，失败返回None
    '''
    result = re.search(mode, html, re.S)
    if result:
        return result.group(1)


def _copy(qq: str) -> None:
    '''
    从 _daledou.yaml 文件复制一份 qq.yaml 文件
    '''
    srcpath = f'{_YAML_PATH}/_daledou.yaml'
    yamlpath = f'{_YAML_PATH}/{qq}.yaml'
    if not path.isfile(yamlpath):
        copy(srcpath, yamlpath)


def _login(cookie: str) -> str | None:
    '''
    验证大乐斗cookie是否有效
    '''
    try:
        url = 'https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?cmd=index'
        headers = {
            'Cookie': cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        }
        for _ in range(3):
            res = requests.get(url, headers=headers)
            res.encoding = 'utf-8'
            html = res.text
            if '商店' in html:
                return html
    except Exception:
        ...


def _defaults(cookie: str) -> str | None:
    '''
    验证cookie
    添加环境变量
    创建文件
    '''
    html: str = _login(cookie)
    if html is None:
        # cookie无效
        return

    # 匹配
    qq: str = _search(r'uin=o(\d+);', cookie)
    rank: str = _search(r'等级:(\d+)', html)
    combat_power: str = _search(r'战斗力</a>:(\d+)', html)

    # 添加环境变量
    environ['QQ'] = qq
    environ['RANK'] = rank
    environ['combat_power'] = combat_power

    # 创建 qq 命名的 yaml 文件
    _copy(qq)

    return qq


def _daledouone():
    reload(settings)
    for cookie in settings.DALEDOU_COOKIE:
        if qq := _defaults(cookie):
            logger.info(f'开始运行第一轮账号：{qq}')
            msg: list = DaLeDouOne().main(cookie)
            pushplus(f'第一轮 {qq}', msg)
        else:
            _error(cookie)


def _daledoutwo():
    reload(settings)
    for cookie in settings.DALEDOU_COOKIE:
        if qq := _defaults(cookie):
            logger.info(f'开始运行第二轮账号：{qq}')
            msg: list = DaLeDouTwo().main(cookie)
            pushplus(f'第二轮 {qq}', msg)
        else:
            _error(cookie)


def _daledoucookie():
    reload(settings)
    for cookie in settings.DALEDOU_COOKIE:
        if qq := _defaults(cookie):
            logger.info(f'账号：{qq} 将在 13:01 和 20:01 运行...')
        else:
            _error(cookie)


def _getenvqq() -> str | None:
    return getenv('QQ')


def _readyaml(key: str, filename: str) -> dict:
    '''
    读取 config 目录下的 yaml 配置文件
    '''
    with open(f'{_YAML_PATH}/{filename}.yaml', 'r', encoding='utf-8') as fp:
        users: dict = yaml.safe_load(fp)
        data: dict = users[key]
    return data

# def _writeyaml(filename, dict):
#     '''
#     写入 config 配置文件
#     '''
#     try:
#         with open(f'./src/config/{filename}.yaml', 'w', encoding='utf-8') as fp:
#             yaml.dump(dict, fp)
#     except Exception as e:
#         logger.error(f'【config】：写入错误 {e}')