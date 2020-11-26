# Virmach_spider
在黑五期间爬取virmach的特价机并下单
# 执行方式
每一个账户开启一个进程，在后台等待主进程发送最新机器的配置信息，如果配置满足预设的条件，则下单（暂无提醒功能）
# 使用方法：
## 增加账户配置
每一个账户的配置信息为一个函数，命名规则为account_xxx, 其中函数名必须以“account_”为首，“xxx”可以任意写，但不能重复
配置函数中的configures支持多个配置信息，每个配置信息为一个字典，修改字典的值即可
配置函数中的just_buy_one为每个账户的购买数量，目前只支持无限个或一个
## 执行方法
1.安装必要库
 pip install -r requirements.txt
2. 安装Chrome或Firefox driver，可在line:58修改
3. python virmach.py
