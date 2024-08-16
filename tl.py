import subprocess
import threading
import requests
import time
from datetime import datetime, timedelta
import pytz

# 定义中国时区
china_tz = pytz.timezone('Asia/Shanghai')

# 定义一个函数来启动FFmpeg进程
def start_ffmpeg(input_url, output_url, comment, processes, retry_count=10):

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
                #print(line)
                if "Error" in line or "failed" in line or "404 Not Found" in line or "403 Forbidden" in line:
                    raise Exception("FFmpeg error detected")
            process.wait()
            break  # 如果成功，跳出循环
        except Exception as e:
            # 停止当前有错误的进程
            if process.poll() is None:  # 检查进程是否仍在运行
                process.terminate()  # 终止进程
                process.wait()  # 等待进程完全结束

            retry_count -= 1
            if retry_count == 0:
                print(f"An error occurred while streaming {comment} {input_url}: {e}. All retry attempts failed.")
            else:
                print(f"An error occurred while streaming {comment} {input_url}: {e}. Retrying... ({retry_count} attempts left)")
                time.sleep(1)  # 等待1秒后重试


# 从指定URL读取输入流和推流地址
def get_streams(url):
    response = requests.get(url)
    response.encoding = 'utf-8'  # 强制将编码设置为 UTF-8
    lines = response.text.strip().splitlines()
    streams = []
    for line in lines:
        # 去除行尾的注释部分
        if '#' in line:
            line, comment = line.split('#', 1)
        else:
            comment = "Unknown Channel"  # 如果没有注释，使用默认名称

        # 去除空白字符
        line = line.strip()
        if not line:
            continue  # 如果是空行，跳过

        # 解析输入流和输出流
        parts = line.split(',')
        if len(parts) != 2:
            print(f"Skipping malformed line: {comment.strip()}")
            continue  # 如果行格式不正确，跳过

        input_url, output_url = parts
        streams.append((input_url.strip(), output_url.strip(), comment.strip()))

    return streams


# 启动推流线程
def start_streaming_threads(streams, processes):
    threads = []
    for input_url, output_url, channel_name in streams:
       # print(f"Starting stream for channel: {channel_name}", flush=True)
        thread = threading.Thread(target=start_ffmpeg, args=(input_url, output_url, channel_name, processes))
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
def main(url):
    processes = []

    # 启动脚本时立即执行一次推流
    streams = get_streams(url)
    start_streaming_threads(streams, processes)

    while True:
        # 获取当前中国北京时间
        now = datetime.now(china_tz)

        # 等待直到下一个整点
        next_hour = get_next_hour()
        time_to_wait = (next_hour - now).total_seconds()
        print(f"Waiting until {next_hour.strftime('%H:%M:%S CST')} to update streams...", flush=True)
        time.sleep(time_to_wait)

        # 停止当前的推流进程
        stop_streaming_threads(processes)

        # 清空进程列表
        processes.clear()

        # 读取流地址并启动新的推流线程
        streams = get_streams(url)
        start_streaming_threads(streams, processes)

# 设置URL
url = 'http://8.138.87.43:2020/源/tl.txt'

# 启动主循环
main(url)
