# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import re

from .default import NexusPHP

ask_dict = {
    "401": ["cname", "ename", "issuedate", "language", "format", "subsinfo", "district"],  # 电影
    "402": ["cname", "ename", "tvalias", "tvseasoninfo", "specificcat", "format", "subsinfo", "language"],  # 剧集
    "403": ["cname", "ename", "issuedate", "tvshowscontent", "tvshowsguest", "district", "subsinfo", "language",
            "format", "tvshowsremarks"],  # 综艺
    "404": ["cname", "ename", "issuedate", "version", "specificcat", "format"],  # 资料
    "405": ["cname", "ename", "issuedate", "animenum", "substeam", "specificcat", "format",
            "resolution", "district"],  # 动漫
    "407": ["issuedate", "cname", "ename", "language", "specificcat", "format", "resolution"],  # 体育
    "408": ["cname", "ename", "issuedate", "version", "specificcat", "format", "language"],  # 软件
    "409": ["cname", "ename", "company", "platform", "specificcat", "language", "format"],  # 游戏
    "411": ["cname", "ename", "specificcat", "format", "subsinfo", "language"],  # 纪录片
    "412": ["cname", "ename", "language", "subsinfo", "district"],  # 移动视频
    "410": ["specificcat", "cname", "format", "tvshowsremarks"],  # 其他
}


class TJUPT(NexusPHP):
    url_host = "http://pt.tju.edu.cn"
    db_column = "pttracker6.tju.edu.cn"

    def exist_torrent_title(self, tag):
        torrent_file_page = self.page_torrent_info(tid=tag, bs=True)
        if re.search("你没有该权限！", torrent_file_page.text):
            torrent_page = self.page_torrent_detail(tid=tag, bs=True)
            torrent_title = re.search("\[TJUPT\]\.(?P<name>.+?)\.torrent", torrent_page.text).group("name")
        else:  # Due to HIGH Authority (Ultimate User) asked to view this page.
            # TODO not test....
            torrent_file_info_table = torrent_file_page.find("ul", id="colapse")
            torrent_title = re.search("\\[name\] \(\d+\): (?P<name>.+?) -", torrent_file_info_table.text).group("name")
        return torrent_title

    def torrent_clone(self, tid):
        """
        Use Internal API: - http://pt.tju.edu.cn/upsimilartorrent.php?id={tid} ,Request Method: GET
                          - http://pt.tju.edu.cn/catdetail_edittorrents.php?torid={id} ,Request Method: GET
        Will response two pages about this clone torrent's information,
        And this function will sort those pages to a pre-reseed dict.
        """
        res_dic = {}
        page_clone = self.get_page(url="{host}/upsimilartorrent.php".format(host=self.url_host),
                                   params={"id": tid}, bs=True)
        if not re.search("没有找到这个种子", page_clone.text):
            logging.info("Got clone torrent's info,id: {tid}".format(tid=tid))
            res_dic.update({"clone_id": tid})

            type_select = page_clone.find("select", id="oricat")
            type_value = type_select.find("option", selected="selected")["value"]

            raw_descr = page_clone.find("textarea", id="descr").text
            raw_descr = re.sub(r"\[code.+?\[/code\]", "", raw_descr, flags=re.S)
            raw_descr = re.sub(r"\[quote.+?\[/quote\]", "", raw_descr, flags=re.S)
            raw_descr = re.sub(r"\u3000", " ", raw_descr)

            url = page_clone.find("input", attrs={"name": "url"})

            res_dic.update({"type": type_value, "descr": raw_descr, "url": url["value"]})

            for name in ["source_sel", "team_sel"]:
                tag = page_clone.find("select", attrs={"name": name})
                tag_selected = tag.find("option", selected=True)
                res_dic.update({name: tag_selected["value"]})

            # Get torrent_info page and sort this page's information into the pre-reseed dict.
            catdetail_page = self.get_page(url="{host}/catdetail_edittorrents.php".format(host=self.url_host),
                                           params={"torid": tid}, bs=True)

            for ask_tag_name in ask_dict[type_value]:
                value = ""
                if catdetail_page.find("input", attrs={"name": ask_tag_name}):
                    tag = catdetail_page.find("input", attrs={"name": ask_tag_name})
                    value = tag["value"]
                elif catdetail_page.find("select", attrs={"name": ask_tag_name}):
                    tag = catdetail_page.find("select", attrs={"name": ask_tag_name})
                    tag_selected = tag.find("option", selected=True)
                    if tag_selected:
                        value = tag_selected["value"]
                res_dic.update({ask_tag_name: value})

        return res_dic

    def data_raw2tuple(self, torrent, torrent_name_search, raw_info: dict):
        torrent_file_name = re.search("torrents/(.+?\.torrent)", torrent.torrentFile).group(1)
        post_tuple = ()
        if int(raw_info["type"]) == 401:  # 电影
            pass
        elif int(raw_info["type"]) == 402:  # 剧集
            post_tuple = (  # Submit form
                ("id", ('', str(raw_info["clone_id"]))),
                ("quote", ('', str(raw_info["clone_id"]))),
                ("file", (torrent_file_name, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
                ("type", ('', str(raw_info["type"]))),
                ("cname", ('', str(raw_info["cname"]))),  # 中文名
                ("ename", ('', torrent_name_search.group("full_name"))),  # 英文名
                ("tvalias", ('', str(raw_info["tvalias"]))),  # 别名
                ("tvseasoninfo", ('', str(raw_info["tvseasoninfo"]))),  # 剧集季度信息
                ("specificcat", ('', str(raw_info["specificcat"]))),  # 剧集类型
                ("format", ('', str(raw_info["format"]))),  # 剧集文件格式
                ("subsinfo", ('', str(raw_info["subsinfo"]))),  # 字幕情况
                ("language", ('', str(raw_info["language"]))),  # 剧集语言
                ("url", ('', str(raw_info["url"]))),  # IMDb链接
                ("nfo", ('', '')),  # 实际上并不是这样的，但是nfo一般没有，故这么写
                ("color", ('', '0')),  # Tell me those three key's function~
                ("font", ('', '0')),
                ("size", ('', '0')),
                ("descr", ('', self.extend_descr(torrent=torrent, info_dict=raw_info))),  # 简介*
                ("getDescByTorrentId", ('', "")),
                ("source_sel", ('', str(raw_info["source_sel"]))),  # 质量
                ("team_sel", ('', str(raw_info["team_sel"]))),  # 内容
                ("visible", ('', "1")),  # 在浏览页面显示(不勾选设置成断种)
                ("uplver", ('', self.uplver)),
            )
        elif int(raw_info["type"]) == 403:  # 综艺
            pass
        elif int(raw_info["type"]) == 404:  # 资料
            pass
        elif int(raw_info["type"]) == 405:  # 动漫
            post_tuple = (  # Submit form
                ("id", ('', str(raw_info["clone_id"]))),
                ("quote", ('', str(raw_info["clone_id"]))),
                ("file", (torrent_file_name, open(torrent.torrentFile, 'rb'), 'application/x-bittorrent')),
                ("type", ('', str(raw_info["type"]))),
                ("cname", ('', str(raw_info["cname"]))),  # 中文名
                ("ename", ('', torrent_name_search.group("full_name"))),  # 英文名
                ("issuedate", ('', str(raw_info["issuedate"]))),  # 发行时间
                ("animenum", ('', torrent_name_search.group("episode"))),  # 动漫集数
                ("substeam", ('', str(raw_info["substeam"]))),  # 字幕组/漫画作者/专辑艺术家
                ("specificcat", ('', str(raw_info["specificcat"]))),  # 动漫类别
                ("format", ('', str(raw_info["format"]))),  # 动漫文件格式
                ("resolution", ('', str(raw_info["resolution"]))),  # 画面分辨率
                ("district", ('', str(raw_info["district"]))),  # 动漫国别
                ("url", ('', str(raw_info["url"]))),  # IMDb链接
                ("nfo", ('', '')),  # 实际上并不是这样的，但是nfo一般没有，故这么写
                ("color", ('', '0')),  # Tell me those three key's function~
                ("font", ('', '0')),
                ("size", ('', '0')),
                ("descr", ('', self.extend_descr(torrent=torrent, info_dict=raw_info))),  # 简介*
                ("getDescByTorrentId", ('', "")),
                ("source_sel", ('', str(raw_info["source_sel"]))),  # 质量
                ("team_sel", ('', str(raw_info["team_sel"]))),  # 内容
                ("visible", ('', "1")),  # 在浏览页面显示(不勾选设置成断种)
                ("uplver", ('', self.uplver)),
            )
        elif int(raw_info["type"]) == 407:  # 体育
            pass
        elif int(raw_info["type"]) == 408:  # 软件
            pass
        elif int(raw_info["type"]) == 409:  # 游戏
            pass
        elif int(raw_info["type"]) == 410:  # 其他
            pass
        elif int(raw_info["type"]) == 411:  # 纪录片
            pass
        elif int(raw_info["type"]) == 412:  # 移动视频
            pass

        return post_tuple
