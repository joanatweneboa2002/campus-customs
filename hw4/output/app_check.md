# Campus Customs: App Check

Three screenshots from the running site, each showing one feature working end to end.
(The same page as [`app_check.html`](app_check.html), in Markdown so the screenshots display when browsing this repository on GitHub.)

## 1. Chat gives the real stock from the database

![Buddy the chatbot answering a stock question on a product page, next to the size and stock boxes](app_check_images/inventory.png)

**Proves:** Buddy never guesses stock. Every number he gives comes live from the database, so a shopper is never told a sold-out size is available. **How you can tell:** his answer (20 in L, 5 in XXL, M sold out) matches the size boxes on the same page and the `inventory` table exactly.

## 2. Hoodie cards pop up after asking the chat

![The Products page filled with hoodie cards under a Buddy's picks banner after asking the chat what hoodies we have](app_check_images/search_cards.png)

**Proves:** the chatbot can drive the website, not just reply in text: a question in the chat turns into real, clickable product cards on the page. **How you can tell:** after asking "what hoodies do you have?" the page switched to "Buddy's picks" with 12 hoodie cards (photo, name, price, info), and each one opens its detail page.

## 3. Stock badges on the product cards (Problem 9)

![Product cards showing a Low stock badge and size strips with sold-out sizes crossed out](app_check_images/usability.png)

**Proves:** shoppers can see what's available before they click, so they don't waste clicks on a product that's sold out in their size. **How you can tell:** sold-out sizes are crossed out and nearly-gone sizes are amber on every card, matching the `inventory` table, and low items get a "Low stock" badge. No product is sold out in *every* size yet, so the all-sizes "Sold out" badge doesn't appear.
