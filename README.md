Main.py has the testable code

You need:

St Louis Fed bank API Key

---It's my personal API key from ST Louis, but it's a formality to just add email to get.
---I'll share mine in the Canvas comment section.

Finviz API key

Go to elite.finviz.com
-> On top left, press account name
-> On dropdown, press settings
-> Look at the headers and select API
-> Find the API Token at the bottom.

Bugs <- If the resulting csv file shows up as a single line with an oauth requests form,
then it is likely that the token for the FinViz API regenerated and you would need to get the new one.

To run the code, you can adjust the values at the end of the Main function 
 - Tick is the tracker for a company's stocks
 - Num Fridays is the range of expiration dates to track
 - Keys mentioned above
