# app/services/web_search_service.py

import os
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# 加载 .env 文件中的环境变量
load_dotenv()

class WebSearchService:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        if not self.api_key:
            print("警告: 未找到 SERPAPI_KEY 环境变量。网络搜索功能将不可用。")

    def _professional_fetch_page_text(self, url: str) -> Optional[str]:
        """
        专业版网页爬虫，专注于提取核心文章内容。
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            # 确保内容是HTML
            if 'text/html' not in response.headers.get('Content-Type', ''):
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # --- 智能移除常见无关区域 ---
            # 移除页眉, 页脚, 导航栏, 侧边栏, 表单, 脚本, 样式等
            for element in soup(["header", "footer", "nav", "aside", "form", "script", "style", "button", "iframe"]):
                element.decompose()
            
            # 尝试找到文章主体 (很多网站会用<article>或id="main", id="content"等)
            body = soup.find('article') or \
                   soup.find(id='content') or \
                   soup.find(id='main') or \
                   soup.find('main') or \
                   soup.body

            if not body:
                body = soup # 如果都找不到，退回到整个soup

            # 获取所有段落<p>的文本
            paragraphs = body.find_all('p')
            if len(paragraphs) < 3: # 如果段落太少，可能提取错了，退回到获取全部文本
                text = body.get_text(separator='\n', strip=True)
            else:
                text = '\n'.join(p.get_text(strip=True) for p in paragraphs)

            # 最终清理
            lines = (line.strip() for line in text.splitlines())
            # 移除太短的、可能是菜单项或按钮的行
            meaningful_lines = (line for line in lines if len(line.split()) > 3) 
            cleaned_text = '\n'.join(meaningful_lines)
            
            return cleaned_text if cleaned_text else None

        except requests.exceptions.RequestException as e:
            print(f"爬取网页 {url} 失败 (网络请求错误): {e}")
            return None
        except Exception as e:
            print(f"处理网页 {url} 失败 (解析错误): {e}")
            return None


    def get_disease_info_from_web(self, disease_label: str, lang: str = 'en') -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None

        query = disease_label.replace("_", " ").replace("___", " ")
        lang_code_map = {'zh': 'zh-cn', 'ms': 'ms'}
        hl = lang_code_map.get(lang, 'en')

        params = {
            "api_key": self.api_key,
            "engine": "google",
            "q": f"{query} disease symptoms and treatment agriculture", # 增加 'agriculture' 提高相关性
            "hl": hl,
            "num": 5 # 获取前5个结果以增加找到好文章的机会
        }

        try:
            print(f"正在执行网络搜索: '{params['q']}' (语言: {hl})...")
            search = GoogleSearch(params)
            results = search.get_dict()
            
            summary, source_url, full_text = None, None, None

            # 遍历有机结果，找到第一个可以成功爬取的、非社交媒体或视频网站的文章
            if "organic_results" in results:
                for result in results["organic_results"]:
                    link = result.get("link")
                    domain = urlparse(link).netloc
                    
                    # 排除不想要的域名
                    if not link or any(bad_domain in domain for bad_domain in ['youtube.com', 'facebook.com', 'twitter.com', 'pinterest.com']):
                        continue
                    
                    print(f"正在尝试从源URL提取全文: {link}")
                    full_text = self._professional_fetch_page_text(link)
                    
                    if full_text: # 如果成功提取到有意义的文本
                        summary = result.get("snippet")
                        source_url = link
                        print(f"✅ 全文提取成功。")
                        break # 找到了就停止
            
            if summary:
                return {
                    "source_url": source_url,
                    "summary_from_web": summary,
                    "full_text_from_web": full_text
                }
            else:
                print("❌ 未能从任何搜索结果中成功提取到全文内容。")

        except Exception as e:
            print(f"❌ 网络搜索或处理时发生严重错误: {e}")
        
        return None

# 创建一个全局实例
web_search_service = WebSearchService()