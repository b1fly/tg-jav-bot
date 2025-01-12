# -*- coding: UTF-8 -*-
import sys
import typing

sys.path.append('..')
import common

BASE_URL = 'https://sukebei.nyaa.si'


def sort_magnets(magnets: list) -> list:
    # 统一单位为 MB
    for magnet in magnets:
        size = magnet['size']
        gb_idx = size.lower().find('gib')
        mb_idx = size.lower().find('mib')
        if gb_idx != -1:  # 单位为 GB
            magnet['size_no_unit'] = float(size[:gb_idx]) * 1024
        elif mb_idx != -1:  # 单位为 MB
            magnet['size_no_unit'] = float(size[:mb_idx])
    # 根据 size_no_unit 大小排序
    magnets = sorted(magnets, key=lambda m: m['size_no_unit'], reverse=True)
    return magnets


def get_nice_magnets(magnets: list, prop: str, expect_val: any) -> list:
    '''过滤磁链列表

    :param list magnets: 要过滤的磁链列表
    :param str prop: 过滤属性
    :param any expect_val: 过滤属性的期望值
    :return list: 过滤后的磁链列表
    '''
    # 已经无法再过滤
    if len(magnets) == 0:
        return []
    if len(magnets) == 1:
        return magnets
    # 开始过滤
    magnets_nice = []
    for magnet in magnets:
        if magnet[prop] == expect_val:
            magnets_nice.append(magnet)
    # 如果过滤后已经没了，返回原来磁链列表
    if len(magnets_nice) == 0:
        return magnets
    return magnets_nice


def get_av_by_id(id: str,
                 is_nice: bool,
                 is_uncensored: bool,
                 magnet_max_count=100) -> typing.Tuple[int, dict]:
    '''通过 sukebei 获取番号对应 av

    :param str id: 番号
    :param bool is_nice: 是否过滤出高清，有字幕磁链
    :param bool is_uncensored: 是否过滤出无码磁链
    :param int magnet_max_count: 过滤后磁链的最大数目
    :return tuple[int, dict]: 状态码和 av
    av格式:
    {
        'id': '',      # 番号
        'title': '',   # 标题
        'img': '',     # 封面地址 | sukebei 不支持
        'date': '',    # 发行日期 | sukebei 不支持
        'tags': '',    # 标签 | sukebei 不支持
        'stars': [],   # 演员 | sukebei 不支持
        'magnets': [], # 磁链
    }
    磁链格式:
    {
        'link': '', # 链接
        'size': '', # 大小
        'hd': '0',  # 是否高清 0 否 | 1 是 | sukebei 不支持
        'zm': '0',  # 是否有字幕 0 否 | 1 是 | sukebei 不支持
        'uc': '0',  # 是否未经审查 0 否 | 1 是
        'size_no_unit': 浮点值 # 去除单位后的大小值，用于排序，当要求过滤磁链时会存在该字段
    }
    演员格式: | sukebei 不支持
    {
        'name': '', # 演员名称
        'link': ''    # 演员链接
    }
    '''
    # 初始化数据
    av = {
        'id': id,
        'title': '',
        'img': '',
        'date': '',
        'tags': '',
        'stars': [],
        'magnets': [],
    }
    # 查找av
    url = f'{BASE_URL}?q={id}'
    code, resp = common.send_req(url)
    if code != 200:
        return code, None
    # 获取soup
    soup = common.get_soup(resp)
    torrent_list = soup.find(class_='torrent-list')
    if not torrent_list:
        return 404, None
    # 开始解析
    trs = torrent_list.tbody.find_all('tr')
    if not trs:
        return 404, None
    try:
        for i, tr in enumerate(trs):
            tds = tr.find_all('td')
            magnet = {
                'link': '',  # 链接
                'size': '',  # 大小
                'hd': '0',  # 是否高清 0 否 | 1 是
                'zm': '0',  # 是否有字幕 0 否 | 1 是
                'uc': '0',  # 是否未经审查 0 否 | 1 是
            }
            for j, td in enumerate(tds):
                if j == 1:  # 获取标题
                    title = td.a.text
                    if 'uncensor' in title or '無修正' in title or '无修正' in title or '无码' in title:
                        magnet['uc'] = '1'
                    if i == 0: av['title'] = title
                if j == 2:  # 获取磁链
                    magnet['link'] = td.find_all('a')[-1]['href']
                if j == 3:  # 获取大小
                    magnet['size'] = td.text
            av['magnets'].append(magnet)
        # 过滤番号
        if is_uncensored:
            av['magnets'] = get_nice_magnets(av['magnets'],
                                             'uc',
                                             expect_val='1')
        if is_nice:
            magnets = av['magnets']
            if len(magnets) > magnet_max_count:
                magnets = magnets[0:magnet_max_count]
            magnets = sort_magnets(magnets)
            av['magnets'] = magnets
    except Exception:
        return 404, av
    return 200, av


if __name__ == '__main__':
    # res = get_av_by_id(id='fc2-ppv-880652', is_nice=True, is_uncensored=False, magnet_max_count=3)
    # res = get_av_by_id(id='stars-080', is_nice=True, is_uncensored=True, magnet_max_count=3)
    res = get_av_by_id(id='ipx-369',
                       is_nice=True,
                       is_uncensored=True,
                       magnet_max_count=3)
    # res = get_av_by_id(id='880652', is_nice=True, magnet_max_count=3)
    # res = get_av_by_id(id='siro-3352', is_nice=True, magnet_max_count=3)
    if res: print(res)