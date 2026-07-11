I want to limit the edits per day:
free tier - 10 edits total with 2 per minuites limit
pro tier - 30 edits total with 5 per minuites limit
premium tier - 10000 edits total with 20 per minuite limit
--
I want to be able to set the models to be used in the config.py, making it more central and easy to configure in the environment and database
edit_model should use gemini-3.1-flash-lite
generation_model should use the gemini-3.5-flash (used in react_website_generator.py line 920 only)  for the actual generation and 3.1-flash-lite for the others
--
The image in the attachment shows the element detected. However, it doesnt tell me what page Im currently going to be touching, and if its a component, like the button, header, it should edit that if its specified or implied in the edit chat.
--
I want to redesign the edit ui, making it more user friendly with focus on the preview to be edited and the sidebar and its components, The topbar should be slimer with the icons and text at the top smaller
Do you think I have everything to build a platform that can build any frontend website and edit it properly?

ensure to /grill-me  if you need clarification. 
--

Upgrade the generation page, I tried to run this prompt "Create a comprehensive website just like this - https://joof-murex.vercel.app
It should be a complete replica of it with the logo and the colors theme and font"
But it creates something entirely different.The AI should always try to understand the intent and if it cannot do so, it can ask for feedback.
--

I want to make this file usable for gemini, chatgpt and claude models (I think the @backend/app/services/prompt_open_ai.py  file is where all that happens for the entire application) -  confirm this for me, of which the config.py models used can be interchanged at any time by me. We have done gemini but harden the @backend/app/services/prompt_open_ai.py  file to support chatgpt and claude models.

Also if the model does not exist in the cost calculator, bypass that, it should not stop the application from working as it should.