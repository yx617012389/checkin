# -*- coding:utf-8 -*-
# -------------------------------
# @Author : github@wh1te3zzz https://github.com/wh1te3zzz/checkin
# @Time : 2025-06-19 09:06:56
# 顺丰速运任务脚本
# -------------------------------
"""
顺丰任务
自行app捉包提取请求头中的url，多账号换行隔开
export sfsyUrl=https://mcs-mimp-web.sf-express.com/mcs-mimp/share/weChat/shareGiftReceiveRedirect?xxxx=xxxx&xxxxx;

cron: 15 8,16 * * *
const $ = new Env("顺丰速运");
"""
import asyncio
import hashlib
import os
import time
import httpx

class SFExpress:
    """
    顺丰速运任务
    """

    def __init__(self, url, timeout, proxy_url=None):
        self.base_url = 'https://mcs-mimp-web.sf-express.com'
        self.login_url = url
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/116.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI "
                          "MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090b11)XWEB/9185",
            "content-type": "application/json",
            "accept": "application/json, text/plain, */*",
            "platform": "MINI_PROGRAM",
            "syscode": "MCS-MIMP-CORE",
            "channel": "wxwd26mem1",
        }
        if proxy_url:
            self.client = httpx.AsyncClient(http2=True, headers=headers, proxy=proxy_url)
        else:
            self.client = httpx.AsyncClient(http2=True, headers=headers)
        self.timeout = timeout

    def signature(self):
        token = 'wwesldfs29aniversaryvdld29'
        timestamp = str(int(time.time() * 1000))
        text = "token=" + token + "&timestamp=" + timestamp + "&sysCode=" + self.client.headers.get("syscode")
        signature = hashlib.md5(text.encode()).hexdigest()
        self.client.headers.update({'timestamp': timestamp, 'signature': signature})

    async def sign(self):

        data = await self.post(
            '/mcs-mimp/commonPost/~memberNonactivity~integralTaskSignPlusService~automaticSignFetchPackage',
            {"comeFrom": "vioin", "channelFrom": "WEIXIN"})
        if data['success']:
            print(f'已连续签到{data["countDay"]}天!')
        else:
            print("签到失败")

    async def post(self, path, params=None):
        self.signature()
        try:
            if params is None:
                params = {}
            url = f'{self.base_url}{path}'
            response = await self.client.post(url, json=params)
            data = response.json()
            if not data['success']:
                return data
            data = data['obj']
            if isinstance(data, dict):
                data['success'] = True
            else:
                data = {'data': data, 'success': True}
            return data
        except Exception as e:
            print(e.args)
            return {
                "success": False,
                "errorMessage": "POST请求异常!"
            }

    async def login(self):
        await self.client.get(self.login_url)
        data = await self.post('/mcs-mimp/ifLogin')
        if not data['success']:
            return -1
        return data['loginStatus']

    async def get_user_info(self):
        """
        :return:
        """
        data = await self.post('/mcs-mimp/commonPost/~memberIntegral~userInfoService~personalInfoNew')
        return data

    async def get_member_day_task(self):
        """
        :return:
        """
        params = {
            "activityCode": "MEMBER_DAY",
            "channelType": "MINI_PROGRAM"
        }
        data = await self.post('/mcs-mimp/commonPost/~memberNonactivity~activityTaskService~taskList', params)
        return data

    async def get_member_day_lottery_info(self):
        data = await self.post('/mcs-mimp/commonPost/~memberNonactivity~memberDayIndexService~index')
        return data

    async def member_day_lottery(self):
        data = await self.post('/mcs-mimp/commonPost/~memberNonactivity~memberDayLotteryService~lottery')
        return data

    async def get_task_list(self):
        params = {
            "channelType": "3",
            "deviceId": "0e88cd05-4785-b232"
        }
        data = await self.post(
            '/mcs-mimp/commonPost/~memberNonactivity~integralTaskStrategyService~queryPointTaskAndSignFromES', params)
        return data

    async def finish_task(self, task_code):
        data = await self.post('/mcs-mimp/commonRoutePost/memberEs/taskRecord/finishTask', {
            "taskCode": task_code
        })
        return data

    async def fetch_award(self, task):
        """
        :return:
        """
        params = {
            "strategyId": task['strategyId'],
            "taskId": task['taskId'],
            "taskCode": task['taskCode'],
            "channelType": "3",
            "deviceId": "0e88cd05-4785-b232"
        }
        data = await self.post('/mcs-mimp/commonPost/~memberNonactivity~integralTaskStrategyService~fetchIntegral',
                               params)
        return data

    async def receive_welfare(self, goods_no, task_code):
        """
        :return:
        """
        params = {
            "from": "Point_Mall",
            "orderSource": "POINT_MALL_EXCHANGE",
            "goodsNo": goods_no,
            "quantity": 1,
            "taskCode": task_code
        }
        data = await self.post('/mcs-mimp/commonPost/~memberGoods~pointMallService~createOrder', params)
        return data

    async def get_bee_task_list(self):
        """
        :return:
        """
        data = await self.post('/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~taskDetail')
        return data

    async def bee_finsh_task(self, task_code):
        params = {
            "taskCode": task_code
        }
        data = await self.post('/mcs-mimp/commonPost/~memberEs~taskRecord~finishTask', params)
        return data

    async def get_bee_index_info(self):
        """
        :return:
        """
        data = await self.post('/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~indexData')
        return data

    async def bee_receive_honey(self, task_type):
        params = {
            "taskType": task_type
        }
        data = await self.post('/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~receiveHoney',
                               params)
        return data

    async def get_goods_no(self):
        """
        :return:
        """
        params = {
            "memGrade": 2,
            "categoryCode": "SHTQ",
            "showCode": "SHTQWNTJ"
        }
        data = await self.post('/mcs-mimp/commonPost/~memberGoods~mallGoodsLifeService~list', params)
        for item in data['data']:
            for goods in item['goodsList']:
                if goods['currentStore'] > 0:
                    return goods['goodsNo']
        return ''

    async def bee_game_report(self):
        params = {
            "gatherHoney": 20
        }
        data = await self.post('/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeGameService~gameReport', params)
        return data

    async def run(self):
        login_status = await self.login()
        if login_status != 1:
            print("登录失败, 跳过该账号!")
            await self.client.aclose()
            return

        time.sleep(self.timeout)
        user_info = await self.get_user_info()
        if not user_info['success']:
            print("获取用户信息失败, 跳过该账号!")
            return

        wechat_name = user_info.get('weChatName', '微信昵称未知')
        level_name = user_info.get('levelName', '')
        points = user_info.get('availablePoints', '0')
        print(f'用户昵称:{wechat_name}\n用户等级:{level_name}\n可用积分:{points}')

        time.sleep(self.timeout)

        await self.sign()
        time.sleep(self.timeout)

        data = await self.get_member_day_lottery_info()
        lottery_num = data.get('lotteryNum', 0)
        print(f'26会员日抽奖次数为: {lottery_num}')
        for i in range(lottery_num):
            data = await self.member_day_lottery()
            print('26会员日抽奖结果:', data)
            time.sleep(self.timeout)

        data = await self.get_task_list()
        task_list = data['taskTitleLevels']
        for task in task_list:

            if task['status'] == 3:
                print(f'今日已完成任务:《{task["title"]}》')
                continue
            if '积分兑' in task["title"] or '寄件下单' in task["title"] or '参与积分活动' in task['title']:
                print(f'跳过任务:《{task["title"]}》')
                continue

            if '领任意生活特权福利' in task['title']:
                goods_no = await self.get_goods_no()
                data = await self.receive_welfare(goods_no, task['taskCode'])
            else:
                data = await self.finish_task(task['taskCode'])

            time.sleep(self.timeout)

            if data['success']:
                print(f'成功完成任务:《{task["title"]}》')
                data = await self.fetch_award(task)
                if data['success']:
                    print(f'成功领取任务:《{task["title"]}》奖励, 获得{data["point"]}积分')
                else:
                    print(f'无法领取任务:《{task["title"]}》奖励')
            else:
                print(f'无法完成任务:《{task["title"]}》')

            time.sleep(self.timeout)

        data = await self.get_bee_task_list()
        if not data['success']:
            print('获取采蜜任务列表失败, 退出!')
            return

        for task in data['list']:
            if task['status'] == 3:
                continue
            if task['taskType'] == 'DAILY_VIP_TASK_TYPE':
                goods_no = await self.get_goods_no()
                time.sleep(self.timeout)
                data = await self.receive_welfare(goods_no, task['taskCode'])
                if not data['success']:
                    print("无法完成任务:《领取生活特权》!")
                    continue
                print('成功完成任务:《领取生活特权》!')
                data = await self.bee_receive_honey(task['taskType'])
                print(data)

            if task['taskType'] == 'BROWSER_CENTER_TASK_TYPE':
                data = await self.bee_finsh_task(task['taskCode'])
                time.sleep(self.timeout)
                if not data['success']:
                    print('无法完成任务:《浏览会员中心10秒!》')
                    continue
                print("成功完成任务:《浏览会员中心10秒》")
                data = await self.bee_receive_honey(task['taskType'])
                print(data)

            if task['taskType'] == 'BEES_GAME_TASK_TYPE' and task['count'] < 3:
                for i in range(3 - task['count']):
                    data = await self.bee_game_report()
                    print(f'完成第{i + 1}次采蜜大冒险任务:', data)
                    time.sleep(self.timeout)

            time.sleep(self.timeout)

        user_info = await self.get_user_info()
        wechat_name = user_info.get('weChatName', '微信昵称未知')
        level_name = user_info.get('levelName', '')
        points = user_info.get('availablePoints', '0')

        time.sleep(self.timeout)
        data = await self.get_bee_index_info()
        if not data['success']:
            print('获取蜂蜜信息失败!')
            return
        capacity = data.get('capacity', '未知')
        usable_honey = data.get('usableHoney', '未知')
        print(f'蜜罐容量:{capacity}ml, 当前可用:{usable_honey}ml!\n\n')
        template = '=' * 20 + f'\n用户昵称:{wechat_name}\n用户等级:{level_name}\n用户积分:{points}\n蜜罐容量:{capacity}ml\n可用蜂蜜:{usable_honey}ml\n\n'
        return template


async def main():
    sfsy_url = os.environ.get('sfsyUrl', '')
    sfsy_url_list = sfsy_url.split('\n')
    sfsy_url_list = [i for i in sfsy_url_list if i]
    timeout = int(os.environ.get('sfsyTimeout', 500)) / 1000
    proxy_url = os.environ.get('ProxyUrl', None)

    if len(sfsy_url_list) < 1:
        print('未找到账号信息, 请先配置环境变量sfsyUrl后再来!')
        return

    print(f'检测到{len(sfsy_url_list)}个账号, 开始执行任务!')
    if proxy_url:
        print(f"当前使用代理:{proxy_url}")
    notify_msg = ''
    for url in sfsy_url_list:
        try:
            app = SFExpress(url, timeout, proxy_url)
            template = await app.run()
            notify_msg += "\n" + template
        except Exception as e:
            print(e.args)

    from notify import send
    send("顺丰速运", notify_msg)


if __name__ == '__main__':
    asyncio.run(main())
