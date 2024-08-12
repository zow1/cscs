import subprocess
import threading

# 定义一个函数来启动FFmpeg进程
def start_ffmpeg(input_url, output_url):
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

    try:
        process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE)
        # 读取并打印FFmpeg进程的输出
        while True:
            line = process.stderr.readline().decode('utf-8').strip()
            if not line:
                break
            print(line)
        process.wait()
    except Exception as e:
        print(f"An error occurred while streaming {input_url}: {e}")

# 输入流和对应的推流地址
streams = [
    ('http://zowzow.yundown.cf/泻火星.php?id=74', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb140'),
    ('http://zowzow.yundown.cf/泻火星.php?id=76', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb141'),
    ('http://zowzow.yundown.cf/泻火星.php?id=2', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb142'),
    ('http://zowzow.yundown.cf/泻火星.php?id=2', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb143'),
    ('http://zowzow.yundown.cf/泻火星.php?id=3', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb144'),
    ('http://zowzow.yundown.cf/泻火星.php?id=6', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb145'),
    ('http://zowzow.yundown.cf/泻火星.php?id=19', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb146'),
    ('http://zowzow.yundown.cf/泻火星.php?id=21', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb147'),
    ('http://zowzow.yundown.cf/泻火星.php?id=50', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb148'),
    ('http://zowzow.yundown.cf/泻火星.php?id=55', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb149'),
    ('http://zowzow.yundown.cf/泻火星.php?id=56', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb150'),
    ('http://zowzow.yundown.cf/泻火星.php?id=58', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb151'),
    ('http://zowzow.yundown.cf/泻火星.php?id=59', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb152'),
    ('http://zowzow.yundown.cf/泻火星.php?id=65', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb153'),
    ('http://zowzow.yundown.cf/泻火星.php?id=64', 'rtmp://ali.push.yximgs.com/live/ttt80182503722594288llltwb154'),

    
    
]

# 为每个流启动一个独立的线程来推流
threads = []
for input_url, output_url in streams:
    thread = threading.Thread(target=start_ffmpeg, args=(input_url, output_url))
    thread.start()
    threads.append(thread)

# 等待所有线程结束
for thread in threads:
    thread.join()
