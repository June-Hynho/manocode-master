import asyncio
import json

from camoufox.async_api import AsyncCamoufox

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import print_formatted_text as print

from manocode.sseparser import get_message_chatgpt_patch, parse_chatgpt_patch, custom_parse_sse

def text_to_html(text):
    br = r"""<p><br class="ProseMirror-trailingBreak"></p>"""
    tags = []
    for line in text.splitlines():
        if not line:
            tags.append(br)
            continue
        tags.append(f"<p>{line}</p>")
    return "".join(tags)

def text_to_js(text):
    html = text_to_html(text)
    return f"""document.getElementById("prompt-textarea").innerHTML = {json.dumps(html)};"""

async def mw_js_eval(page, js):
    await page.evaluate(f"mw:{js}")

async def send_prompt(page, text):
    await page.locator("#prompt-textarea").click()
    await mw_js_eval(page, text_to_js(text))

    async with page.expect_response("https://chatgpt.com/backend-anon/f/conversation") as resp_info:
        await page.locator("#composer-submit-button").click()

    response = await resp_info.value
    data = await response.text()

    return parse_chatgpt_patch(custom_parse_sse(data))

async def main():
    prompts = PromptSession()

    async with AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()
        await page.goto('https://chatgpt.com')

        with patch_stdout():
            while True:
                cmd = await prompts.prompt_async("> ")

                if cmd == "exit":
                    break
                else:
                    resp = await send_prompt(page, cmd)
                    print(get_message_chatgpt_patch(resp))

        await browser.close()


def run():
    asyncio.run(main())


if __name__ == '__main__':
    run()
