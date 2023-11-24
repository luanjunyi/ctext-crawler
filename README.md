# ctext-crawler
 
Crawl the book content from ctext.org into JSON format.

For example,

```bash
python crawl.py --url="https://ctext.org/huangdi-neijing/ling-shu-jing/zhs" 
    --title="黄帝内经 - 灵枢经" 
    --chapter-filter-regex="huangdi-neijing/.+/zhs"
```

This will crawl the book 灵枢经 from its root URL(ctext.org/huangdi-neijing/ling-shu-jing/zhs) and store the result in "黄帝内经 - 灵枢经.json".


## Provide URL filter regex

You need to provide the regular expression for each chapter URL in `--chapter-filter-regex`. This regex is used to distinguish chapter links from the root page.

For example, the chapter links from the root page of 灵枢经 are all like `https://ctext.org/huangdi-neijing/xie-qi-cang-fu-bing-xing/zhs`, therefore, a good regex is `huangdi-neijing/.+/zhs`. You can find the pattern from inspecting the HTML of the book's root page, in our example, it's https://ctext.org/huangdi-neijing/ling-shu-jing/zhs.

I know this is not a user friendly way to filter. Sadly, I can't find any pattersn, like class name or page structure, that will work correctly.

# NOTICE

This source code is offered to public for free. Its purpose is education only. Anyone shouldn't use this software to download any significant content from ctext.org. Ctext stated that software downloading in large scale is prohibited and will result in banning. Please reference their orignial link (https://ctext.org/zhs) if you need to use Ctext's content in any way.

Below is their statement from ctext.org website.

```
如果您想引用本网站上的内容，请同时加上至本站的链接：https://ctext.org/zhs。请注意：严禁使用自动下载软体下载本网站的大量网页，违者自动封锁，不另行通知。
```
