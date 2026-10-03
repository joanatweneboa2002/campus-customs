# AI Prompts Log: Homework 4

A record of the prompts I used with Claude Code for each Homework 4 problem.

---

## Problem 1: Vibe coder prompts

**Prompt:**

> Create a file called AI_prompts.md in my project. It's a log of the prompts I use with you for Homework 4. For each homework problem it should have a section with the problem number and title, the prompt I typed, and one follow-up prompt (if any). Start it with a section for Problem 1: Vibe coder prompts.

**Follow-up prompt:**

> The problem we just worked on is Problem 2: Analyze the database. i want you to update every prompt in the promt.md file as i instructed . and update every prompt

**What the first prompt was missing:**

My first prompt didn't say the log had to be updated after every new problem, so I had to ask it to keep adding sections as we went.

---

## Problem 2: Analyze the database

**Prompt:**

> I just downloaded a zip data file 3. Can you see it?

**Follow-up prompt:**

> yes. but an you open the database at data/campus_customs.db and look at the catalogue, inventory and users tables? I want a new file called output/harness.md. For each table, list all the fields and add one short line on why each one matters for the shop or the chatbot. Keep it simple, I'll be adding more to this file later.

**What the first prompt was missing:**

My first prompt only asked if it could see the data file and didn't say what I wanted done with it, so I had to spell out the tables and the harness.md file.

---

## Problem 3: Build the Campus Customs website

**Prompt:**

> Okay, Problem 3: time to build the actual Campus Customs website. Set it up with React + Vite + TypeScript please. I want a nav bar with Home, Products, About Us, Log in and Create account. For Home and About Us, take some vibes from yalebulldogblue.com but write everything fresh, no copying their words. The Products page should pull from data/campus_customs.db and show each item's picture, name, price and a little description. When I click a product, give me a detail page with a big picture on one side and all the info on the other side, like description, price, sizes and stock. Also drop a chat box in the bottom right corner. It doesn't have to work yet, I just want it there. Then set up a simple FastAPI backend in backend/main.py to serve the products and images.

**Follow-up prompt:**

> This is the follow up prompt. its nice and working, but first, the color  code is boring. i want earthly tone colors, yehah? the color palette should be pretty, but not pink and black. Also,  some product pictures aren't loading and the detail page doesn't show sizes or stock. Can you fix the pictures and pull sizes and stock from the inventory table?

**Follow-up prompt 2:**

> Ok, its better. some phots still have unclear pictures. Some are blurry and other.... are just not good. Here's the thing tho;  I DONT WANT THAT!. so make sure all the pictures are clear, and very visible, remove the black shadows from the pictures with black shadows and can you change the outlook of the website. i dont want it to be so plain and serious. Add a little personality; you know cus i have personality.

**What the first prompt was missing:**

I didn't describe the look or the photo quality I wanted, so it came out plain, some pictures didn't load or were blurry, and sizes and stock were missing from the detail page.

---

## Problem 4: Create account and login

**Prompt:**

> Problem 4 now, let's make the Log in and Create account pages actually work. Create account should ask for first name, last name, email, password and confirm password, then save the person in the users table. Log in should just need email and password. Please hash the passwords, I don't want any plain passwords sitting in the database where hackers can see them. Make sure the test user test@campuscustoms.yale.edu with password "password" can log in. Then add a little section to output/harness.md explaining what we save for each user and how the passwords are protected.

**Follow-up prompt:**

> Login works for the test user, but can you double check a brand new account works too? Make one, log out, log back in, and try a wrong password. Also show me what the password looks like in the users table so I know it's hashed.

**What the first prompt was missing:**

I only asked about the test user, so I didn't know for sure that new accounts and wrong passwords worked properly.

---

## Problem 5: PydanticAI agent backend

**Prompt:**

> Problem 5, time to give the chat box a brain! Can you build a PydanticAI agent inside my FastAPI backend and connect it to the chat box on the site? Use the course model through Portkey, my OPEN AI API key is in the .env file. Split it up like this: backend/agent.py sets up the agent, backend/tools.py has the tools, backend/models.py has the types for chat replies and product cards, and backend/prompts/prompt.md has the system prompt. In the prompt, make the bot sound friendly and Campus Customs-y, and add some basic safety rules like staying on topic and never sharing customer info. The backend should run with uvicorn main:app --reload --port 8000. When you're done, add a section to output/harness.md explaining how the website talks to the backend and how the agent loads.

**Follow-up prompt:**

> The chat works, but can you test the full loop? Send a message from the chat box, make sure it reaches the agent and comes back, and check my API key is only in .env and not in any code file.

**What the first prompt was missing:**

I didn't ask it to test the whole path from the chat box to the agent and back, or to check where my API key was stored.

---

## Problem 6: Tools for product info and stock

**Prompt:**

> Problem 6! Right now my chatbot can talk but it doesn't actually know anything about the products lol. Can you add tools in backend/tools.py so the agent can look up a product's description, price and stock (by size too) straight from data/campus_customs.db? It should never make up a price or a number. If a size is sold out, just say it clearly. Update prompts/prompt.md so the agent knows when to use these tools, and add the return types in models.py. Then add a part to output/harness.md describing each tool and why we picked those fields.

**Follow-up prompt:**

> I asked if the hoodie comes in medium and it said yes, but the database says medium is out of stock. Can you make sure it always checks the stock tool before answering anything about sizes?

**What the first prompt was missing:**

I didn't say it had to check stock every single time, so sometimes it just guessed about sizes.

---

## Problem 7: Chat search that updates the page

**Prompt:**

> Problem 7, this one's fun. When someone asks the chatbot something like "what hoodies do you have?", I want the agent to search the catalogue and then the actual website should show those items as product cards, with the picture, name, price and a little info. If I click any of those cards, it should open the same detail page from Problem 3 with the big picture and full info. Have the agent send back the matching products in a structured way so the website can show them as cards. Then update prompts/prompt.md and output/harness.md to explain how the search results get from the chat to the page.

**Follow-up prompt:**

> The cards show up when I ask for hoodies. Can you check that clicking one of the new cards opens the detail page, and that asking for something we don't sell doesn't show random cards? When I tested it, "show me Harvard hoodies" filled the whole page with 12 Yale hoodies, and for socks it said the shop on Broadway "may have more accessories," which it can't know. Please fix both.

**What the first prompt was missing:**

I didn't say what should happen when someone asks for something we don't sell, or ask it to test clicking the new cards. Without that rule, the agent filled the page with substitutes and made up a claim about the store.

---

## Problem 8: Customer memory

**Prompt:**

> let's give the chatbot a memory. When someone is logged in, save their chat history in a new table in the database, and load it back when they come back and log in again. Guests can still chat, their history just doesn't need to be saved. I also want the agent to know who it's talking to, so pass the customer's name and email in the agent deps. And pass the page they're on too, so if someone is looking at a product and asks "do you have this in pink?", the agent knows which product they mean. Then update output/harness.md to explain how chat history is saved, what customer info the agent can see, and how the page info gets passed.

**Follow-up prompt:**

> Can you check that one customer can never see another customer's chat history? Log in as the test user, chat, log out, then log in as someone else and make sure the old chat doesn't show up.

**What the first prompt was missing:**

I didn't say that customers' chats have to stay private from each other, so I had to check it separately.

---

## Problem 9: Usability improvements

**Prompt:**

> Problem 9, now let's make the shop better. I want 4 improvements, 2 on the website and 2 on the agent. Website: first, add "Low stock" and "Sold out" badges on the product cards so people know before they click. Second, put a few suggested questions in the chat box like "What's under $25?" so people know what to ask. Agent: first, if someone wants a size that's sold out, have it suggest something similar that's in stock so we don't lose the sale. Second, make it safer, it should never share another customer's info and should ignore people trying tricks like "ignore your instructions." Write each one up in output/usability.md as you build it, with what we added and why it helps a shopper or the business.

**Follow-up prompt:**

> Lets work on problem 4 now. About github, how do we fix that? then fix the sizing issue you noticed. i like your suggestion

**What the first prompt was missing:**

I didn't say how the sizes should show on the product cards, so I had to come back and fix the sizing issue.

---

## Problem 10: Style the website

**Prompt:**

> Problem 10, let's make this site look like a real Yale shop and not a plain template. I think weve done a major part of this. check the website, is there smth we need to improve? I am particularly worried about the pictures. iF theres smth t improve let me know. Otherwise make it cohesive

**Follow-up prompt:**

> ok great. there is one minor thing tho. The color palette is too bright for my eyes. I want to keep it like this, but lighter, can you changed it? just the color themes, keeo everything else the same

**What the first prompt was missing:**

I didn't say anything about how bright the colors should be, so the palette came out too strong for my eyes.

---

## Problem 11: Site testing (app check)

**Prompt:**

> Problem 11, time to show the site works! I put 3 screenshots in output/app_check_images/: inventory.png, search_cards.png and usability.png. Can you make a simple page at output/app_check.html with a heading for each check, the screenshot under it, and one or two sentences on what it proves? First one shows the chat giving the real stock from the database, second shows the hoodie cards popping up after I asked, third shows the sold out badge from Problem 9. Link the pictures with relative paths like app_check_images/inventory.png so they still show up on GitHub.

**Follow-up prompt:**

> Can you open output/app_check.html and make sure all 3 screenshots load, and that each caption says what the screenshot proves, not just what it shows? The captions explain how it works more than what it proves, so please rewrite them to lead with what each test proves.

**What the first prompt was missing:**

I didn't ask it to check that the images actually load or that the captions explain why each test matters. The images loaded, but the captions described how things work instead of what each test proves.

---

## Problem 12: Audit trail, safety, finish harness

**Prompt:**

> Problem 12, almost done! First, I want an audit trail. Every time the agent does something, add an entry to output/audit_trail.json with the time, which tool it used, a short version of what went in and what came out, and why it stopped. It should only ever add to the file, never wipe it, even when I restart the server. Second, check that prompts/prompt.md has clear safety rules, like stay on topic, never share other customers' info, never make up prices or stock, and ignore people trying to trick it. Third, let's finish output/harness.md. Make sure it explains the fields in models.py and why we chose them, all the tools, the safety rules, and the specs: loop limits, how many results it returns max, which model we use, and how to run the website and the backend.

**Follow-up prompt:**

> Can you restart the backend, send a couple chats, and check that audit_trail.json still has the old entries with the new ones added at the bottom?

**What the first prompt was missing:**

I didn't ask it to test with a restart, so I couldn't be sure the file never gets wiped.

---

## Problem 13: Push to GitHub and submit the URL

**Prompt:**

> Last one, Problem 13! I have a cleaned-up hw4 folder. Please copy my local data folder (campus_customs.db and the product images) into hw4/data so the app still runs on my computer, and copy my .env into hw4/.env. Then replace everything in my campus-customs GitHub repo with this hw4 folder, starting the git history fresh so the old database and images are completely gone. Before pushing, show me the list of files that will be uploaded so I can check there's no .env, .db or images.

**Follow-up prompt:**

> My first push had the database and all the product images on GitHub, which my professor said not to do. Can you make sure the .gitignore blocks .env, data/ and .db files, and show me what's on GitHub after the push so I can check?

**What the first prompt was missing:**

My first time pushing, I didn't tell it what to keep off GitHub or ask to see the file list, so the database and images got uploaded.
