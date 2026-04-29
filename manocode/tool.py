import asyncio
import json

from camoufox.async_api import AsyncCamoufox

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import print_formatted_text as fprint

from manocode.sseparser import get_message_chatgpt_patch, parse_chatgpt_patch, custom_parse_sse
from manocode.prompts import CODING_AGENT
from manocode.intercept import FETCH_HOOK

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


async def on_sse(source, data):
    pass


async def send_prompt(page, text):

    # Why not use locator? because of popups.
    click_textarea_js = """document.getElementById("prompt-textarea").click();"""
    await mw_js_eval(page, click_textarea_js)
    await mw_js_eval(page, text_to_js(text))

    async with page.expect_response("https://chatgpt.com/backend-anon/f/conversation") as resp_info:
        click_submit_js = 'document.getElementById("composer-submit-button").click();'
        await mw_js_eval(page, click_submit_js)

        response = await resp_info.value
        data = await response.text()

    return parse_chatgpt_patch(custom_parse_sse(data))

async def main():
    prompts = PromptSession()

    async with AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()
        await page.expose_binding("python_sse_callback", on_sse)
        await page.goto('https://chatgpt.com')
        await page.evaluate(FETCH_HOOK)
        #print("Initing with CODING_AGENT")
        #resp = await send_prompt(page, CODING_AGENT)
        #print(get_message_chatgpt_patch(resp))

        with patch_stdout():
            while True:
                try:
                    cmd = await prompts.prompt_async("\n\n>>> ", multiline=True)
                except EOFError:
                    print("Prompt me harder next time...")
                    break
                resp = await send_prompt(page, cmd)
                print(get_message_chatgpt_patch(resp))

        await browser.close()


def run():
    asyncio.run(main())


if __name__ == '__main__':
    run()
