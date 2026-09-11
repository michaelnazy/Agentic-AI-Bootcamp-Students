# Module 3 Bridge Project Notes

## A. Where did the budget force a real trade-off?
Because we only had 9 lookups for 7 suppliers, I had to spend extra lookups (Web Searches) on ambiguous suppliers like Almarai and Zorblax that returned NO_RECORDS from the GLEIF register. As a result, the budget ran out before the final suppliers in the queue could be checked by GLEIF. The trade-off was explicitly accepting residual risk on those unassessed suppliers in order to ensure the ambiguous ones were thoroughly vetted, rather than blindly approving them. 

## B. What sanctions threshold did you set, and why?
I set the sanctions similarity threshold to 0.85 in the decision prompt. Legitimate companies on the list scored between 0.71 and 0.81 just for having common words like 'Trading Company' or 'LLC', while the genuinely sanctioned entity (Al Wasel) scored 1.00. A threshold of 0.85 safely clears legitimate businesses while catching exact matches. Setting it too low blocks honest suppliers; setting it too high risks committing a financial crime.

## C. Where did the agent nearly get it wrong?
The agent could have easily fallen for the "Siemens AG" trap by blindly approving it just because the register returned data. To fix this, I engineered the `gleif_lookup` tool to explicitly count and report "exact matches". Because the 5 returned entities were subsidiaries (e.g., Siemens Energy AG) and not an exact match to "Siemens AG", the agent correctly assigned CONDITIONS to ask Procurement for the exact LEI. This demonstrated that the disambiguation must be handled deliberately, not hidden inside the tool.