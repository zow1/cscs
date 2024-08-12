import subprocess
import threading
import requests
import time
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import re

# 定义中国时区
china_tz = pytz.timezone('Asia/Shanghai')

# 定义电视频道映射
n = {
    '1': 'tv-show-20052-3',  # 翡翠台
    '2': 'tv-show-20058-3',  # 明珠台
    # 其他映射...
}

# 获取直播流的函数
def get_liveurl(id):
    url = f'https://www.xhzb.tw/{n[id]}.html'
    response = requests.get(url)
    response.encoding = 'utf-8'
    html_content = response.text
    
    match = re.search(r'<input name="ps" id="ps" type="hidden" value="([^"]+)">', html_content)
    if match:
        psValue = match.group(1)
        post_url = 'https://www.xhzb.tw/get_video.php'
        post_data = {'vu': psValue}
        headers = {
            'Host': 'www.xhzb.tw',
            'Content-Length': '59',
            'sec-ch-ua': '"Chromium";v="123", "Not:A-Brand";v="8"',
            'content-type': 'application/x-www-form-urlencoded',
            'x-requested-with': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
            'origin': 'https://www.xhzb.tw',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': url,
        }
        response = requests.post(post_url, data=post_data, headers=headers)
        response.encoding = 'utf-8'
        match = re.search(r'video-url="([^"]+)', response.text)
        if match:
            liveurl = match.group(1)
            output_url = f'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltw{id}'
            return liveurl, output_url
    return None, None


# 多线程获取所有频道的直播流
def get_all_streams():
    with ThreadPoolExecutor(max_workers=10) as executor:  # 调整 max_workers 控制线程数
        futures = [executor.submit(get_liveurl, id) for id in n]
        streams = [future.result() for future in futures if future.result()[0] and future.result()[1]]
    return streams


# 定义启动FFmpeg进程的函数
def start_ffmpeg(input_url, output_url, processes, retry_count=3):
    ffmpeg_command = [
        'ffmpeg',
        '-re',
        '-stream_loop', '-1',
        '-i', input_url,
        '-bsf:a', 'aac_adtstoasc',
        '-vcodec', 'copy',
        '-acodec', 'copy',
        '-f', 'flv',
        '-y',
        '-reconnect', '1',
        '-reconnect_at_eof', '1',
        '-reconnect_streamed', '1',
        output_url
    ]

    while retry_count > 0:
        try:
            process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE)
            processes.append(process)
            while True:
                line = process.stderr.readline().decode('utf-8').strip()
                if not line:
                    break
                print(line)
                if "Error opening input file" in line or "Conversion failed!" in line:
                    raise Exception("FFmpeg error detected")
            process.wait()
            break  # 如果成功，跳出循环
        except Exception as e:
            retry_count -= 1
            if retry_count == 0:
                print(f"An error occurred while streaming {input_url}: {e}. All retry attempts failed.")
            else:
                print(f"An error occurred while streaming {input_url}: {e}. Retrying... ({retry_count} attempts left)")
                time.sleep(1)  # 等待1秒后重试

# 启动推流线程
def start_streaming_threads(streams, processes):
    threads = []
    for input_url, output_url in streams:
        thread = threading.Thread(target=start_ffmpeg, args=(input_url, output_url, processes))
        thread.start()
        threads.append(thread)
    return threads

# 停止所有正在运行的推流
def stop_streaming_threads(processes):
    for process in processes:
        if process.poll() is None:  # 检查进程是否仍在运行
            process.terminate()  # 终止进程
            process.wait()  # 等待进程完全结束

# 计算下一次整点时间（中国北京时间）
def get_next_hour():
    now = datetime.now(china_tz)
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return next_hour

# 主循环：每整点更新推流地址
def main():
    processes = []

    # 启动脚本时立即执行一次推流
    streams = get_all_streams()
    start_streaming_threads(streams, processes)

    while True:
        # 获取当前中国北京时间
        now = datetime.now(china_tz)

        # 等待直到下一个整点
        next_hour = get_next_hour()
        time_to_wait = (next_hour - now).total_seconds()
        print(f"Waiting until {next_hour.strftime('%H:%M:%S CST')} to update streams...")
        time.sleep(time_to_wait)

        # 停止当前的推流进程
        stop_streaming_threads(processes)

        # 清空进程列表
        processes.clear()

        # 读取流地址并启动新的推流线程
        streams = get_all_streams()
        start_streaming_threads(streams, processes)

# 启动主循环
main()
