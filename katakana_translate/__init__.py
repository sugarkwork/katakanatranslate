import re
import json
import os
import asyncio
from typing import List, Dict
from chat_assistant import ChatAssistant
import asyncio
import pickle
import aiofiles
from json_repair import repair_json

# データをピクル化して非同期にファイルに保存
async def async_pickle_dump(data, filename):
    try:
        async with aiofiles.open(filename, 'wb') as file:
            pickled_data = pickle.dumps(data)
            await file.write(pickled_data)
        print(f"データを {filename} に保存しました。")
    except Exception as e:
        print(f"保存中にエラーが発生: {e}")

# 非同期でピクルファイルからデータをロード
async def async_pickle_load(filename):
    try:
        async with aiofiles.open(filename, 'rb') as file:
            pickled_data = await file.read()
            data = pickle.loads(pickled_data)
        print(f"{filename} からデータをロードしました。")
        return data
    except Exception as e:
        print(f"ロード中にエラーが発生: {e}")
        return None
    
class KatakanaTranslator:
    def __init__(self, model: str = "gemini/gemini-1.5-flash-002"):
        """
        テキスト翻訳クラスの初期化
        
        Args:
            model (str, optional): 使用するAIモデル. デフォルトは"gemini/gemini-1.5-flash-002".
        """
        self.chache = {}
        self.assistant = ChatAssistant()
        self.assistant.model_manager.change_model(model)

    def extract_alphanumeric(self, text: str) -> List[str]:
        """
        テキストから英数字の文字列を抽出する
        
        Args:
            text (str): 入力テキスト
        
        Returns:
            List[str]: 抽出された英数字の文字列リスト
        """
        pattern = r'[a-zA-Z]+(?:\d+(?:\.\d+)*)?(?:\d+)?'
        return re.findall(pattern, text)

    async def translate_to_katakana(self, words: List[str]) -> Dict[str, str]:
        """
        単語リストを日本語カタカナ風に翻訳する
        
        Args:
            words (List[str]): 翻訳する単語リスト
        
        Returns:
            Dict[str, str]: 単語とその翻訳の辞書
        """
        prompt_text = ("次の英単語および数字を英語風のカタカナ読みにするとどうなりますか？\n"
                       "Python の dict 型で出力してください。コメントや補足は不要です。\n")

        response = await self.assistant.chat("", f"{prompt_text}\n\n{words}")
        print(response)
        return json.loads(repair_json(response))    
    

    async def get_cached_translation(self, text: str) -> str:
        """
        キャッシュされた翻訳を取得する
        """
        key = f"translation_{text}"
        if not self.chache:
            if os.path.exists("translation_cache.pkl"):
                self.chache = await async_pickle_load("translation_cache.pkl")
        result = self.chache.get(key, None)
        return result

    async def save_translation(self, text: str, translated_text: str) -> None:
        """
        翻訳をキャッシュする
        """
        key = f"translation_{text}"
        if not self.chache:
            self.chache = {}
        self.chache[key] = translated_text
        await async_pickle_dump(self.chache, "translation_cache.pkl")

    async def translate_text(self, text: str) -> str:
        # 英数字の単語を抽出
        alphanumeric_words = list(set(self.extract_alphanumeric(text)))

        # 英数字の文字列の長い順にソートする
        sorted_words = alphanumeric_words.copy()
        sorted_words.sort(key=lambda x: len(x), reverse=True)

        # キャッシュされた翻訳を取得
        cached_words = {}
        for word in alphanumeric_words:
            translated_text = await self.get_cached_translation(word)
            if translated_text:
                cached_words[word] = translated_text

        # キャッシュされた翻訳をテキストから削除
        for key in cached_words.keys():
            alphanumeric_words.remove(key)

        # カタカナ翻訳を取得
        if alphanumeric_words:
            print("Translating to Katakana...")
            print(alphanumeric_words)
            translates = await self.translate_to_katakana(alphanumeric_words)
        else:
            print("No words to translate.")
            translates = {}
        
        translates.update(cached_words)
        print("Translation completed.")
        print(translates)

        # テキストを置き換え
        for key in sorted_words:
            text = text.replace(key, translates[key])
            if key not in cached_words:
                await self.save_translation(key, translates[key])
    
        return text

async def main():
    # 使用例
    text = """
    LibreChatのデータベース全体をテキスト形式でダンプする方法について、以下の手順を用いることで実現できます。
    Ubuntu20.04にはApache2はプレインストールされていません。
    a123, http://example.com, superuser, 123456
    Ubuntuは、デスクトップ版とサーバー版の2つのEditionがあります。
    Mongoの意味は何ですか？知らんけど。
    """
    
    translator = KatakanaTranslator()
    translated_text = await translator.translate_text(text)

    print("Original text:")
    print(text)
    print("\nTranslated text:")
    print(translated_text)

if __name__ == "__main__":
    asyncio.run(main())