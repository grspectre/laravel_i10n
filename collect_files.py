import os
import argparse
import re
from typing import Dict, Optional, Any
import json
import requests


def config(key: str, name: str = 'config') -> Any:
    config_path = os.path.abspath(os.path.dirname(__file__))
    file_name = os.path.join(config_path, '{}.json'.format(name))
    with open(file_name, 'r', encoding='utf8') as fp:
        data = json.load(fp)
        if key in data:
            return data[key]
    return None


def translate_yandex(input: str) -> Optional[str]:
    # use `yc iam create-token` to get this token
    folder_id = config('folder_id')
    token = config('token')
    body = {
        "targetLanguageCode": 'ru',
        "texts": [input],
        "folderId": folder_id,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {0}".format(token)
    }
    response = requests.post('https://translate.api.cloud.yandex.net/translate/v2/translate',
        json = body,
        headers = headers
    )
    try:
        content = json.loads(response.text)
        return content['translations'][0]['text']
    except KeyError:
        return None


def load_json(path: str, lang: str) -> Dict:
    file_path = os.path.join(path, 'lang', '{}.json'.format(lang))

    if not os.path.exists(file_path):
        return {}
    content = open(file_path, 'r', encoding='utf8').read()
    return json.loads(content)


def save_json(path: str, lang: str, data: Dict) -> None:
    file_path = os.path.join(path, 'lang', '{}.json'.format(lang))

    data = json.dumps(data, indent=2, ensure_ascii=False)
    open(file_path, 'w', encoding='utf8').write(data)


def main(path: str) -> None:
    re_str = re.compile(r"__\('(.+)'\)")
    en_dict = load_json(path, 'en')
    ru_dict = load_json(path, 'ru')

    for root, _, files in os.walk(path):
        for fl in files:
            if fl.endswith('.blade.php'):
                file_path = os.path.join(root, fl)
                content = open(file_path, 'r', encoding='utf8').read()
                if '__(' in content:
                    find_strs = re.findall(re_str, content)
                    for one in find_strs:
                        if one in en_dict and one in ru_dict:
                            continue
                        print("Process '{}'".format(one))
                        if one not in en_dict:
                            en_dict[one] = one
                        if one not in ru_dict:
                            translated_text = translate_yandex(one)
                            if translated_text is not None:
                                ru_dict[one] = translated_text
    save_json(path, 'en', en_dict)
    save_json(path, 'ru', ru_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("collect files")
    parser.add_argument("path", help="An path to laravel installation.", type=str)
    args = parser.parse_args()
    main(args.path)
