import requests
import os
import sys
from tqdm import tqdm

def download_pdf(url, save_path='./'):
    """
    从指定URL下载PDF文件并保存到本地
    
    参数:
    url (str): PDF文件的URL地址
    save_path (str): 保存文件的目录路径，默认为当前目录
    
    返回:
    bool: 下载成功返回True，失败返回False
    """
    try:
        # 创建保存目录
        os.makedirs(save_path, exist_ok=True)
        
        # 从URL中提取文件名
        filename = os.path.join(save_path, url.split('/')[-1])
        
        # 发送HEAD请求获取文件大小
        response = requests.head(url)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        
        # 发送GET请求下载文件
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            
            # 创建进度条
            progress_bar = tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                desc=filename.split('/')[-1],
                file=sys.stdout
            )
            
            # 写入文件并更新进度条
            with open(filename, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        progress_bar.update(len(chunk))
            
            progress_bar.close()
            
        print(f"\n文件已成功下载到: {filename}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")
        return False
    except Exception as e:
        print(f"发生未知错误: {e}")
        return False

if __name__ == "__main__":
    pdf_url = "https://temp.infinitylog.top/AAAYKUHELP/maogai/20250711/%E6%AF%9B%E6%A6%82Binfinity%E5%AE%A2%E8%A7%82%27%27.pdf"
    download_pdf(pdf_url)    