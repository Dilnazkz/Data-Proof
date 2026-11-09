import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 1440, "height": 1000})
        await pg.goto("http://localhost:8599/", wait_until="networkidle"); await pg.wait_for_timeout(6000)
        for name, fn in (("Қазақстан сценарийлері", "6_KZ"), ("Research Results", "7_Research")):
            await pg.get_by_text(name, exact=True).first.click()
            await pg.wait_for_timeout(7000)
            await pg.screenshot(path=f"shots/{fn}.png", full_page=True)
        await b.close()
asyncio.run(main())
