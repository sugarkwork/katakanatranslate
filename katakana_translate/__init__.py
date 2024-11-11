import re
import json
import os
import asyncio
import logging
from typing import List, Dict
from chat_assistant import ChatAssistant
from pmem.async_pmem import PersistentMemory
import asyncio
from json_repair import repair_json


class KatakanaTranslator:
    def __init__(self, model: str = "gemini/gemini-1.5-flash-002", cache_file_name: str = "katakana_translate_cache.db"):
        """
        テキスト翻訳クラスの初期化
        
        Args:
            model (str, optional): 使用するAIモデル. デフォルトは"gemini/gemini-1.5-flash-002".
        """
        self.chache = {}
        self.logger = logging.getLogger(__name__)
        self.memory = PersistentMemory(cache_file_name)
        self.assistant = ChatAssistant(memory=self.memory)
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
        self.logger.debug(response)
        return json.loads(repair_json(response))    
    

    async def get_cached_translation(self, text: str) -> str:
        """
        キャッシュされた翻訳を取得する
        """
        key = f"translation_{text}"
        result = await self.memory.load(key)
        return result

    async def save_translation(self, text: str, translated_text: str) -> None:
        """
        翻訳をキャッシュする
        """
        key = f"translation_{text}"
        await self.memory.save(key, translated_text)

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
            self.logger.debug("Translating to Katakana...")
            self.logger.debug(alphanumeric_words)
            translates = await self.translate_to_katakana(alphanumeric_words)
        else:
            self.logger.debug("No words to translate.")
            translates = {}
        
        translates.update(cached_words)

        self.logger.debug("Translation completed.")
        self.logger.debug(translates)

        # テキストを置き換え
        for key in sorted_words:
            text = text.replace(key, translates[key])
            if key not in cached_words:
                await self.save_translation(key, translates[key])
    
        return text

async def main():
    # 使用例
    text = """
    LibreChatのdatabase全体をtext形式でdumpする方法について、以下の手順を用いることで実現できます。
    Ubuntu20.04にはApache2はpreinstallされていません。
    a123, http://example.com, superuser, 123456
    Ubuntuは、Desktop版とServer版の2つのEditionがあります。
    Mongoの意味は何ですか？知らんけど。GEMINI_API_KEY
    """

    print("Original text:")
    print(text)
    
    translator = KatakanaTranslator()
    translated_text = await translator.translate_text(text)

    print("\nTranslated text:")
    print(translated_text)

    await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())