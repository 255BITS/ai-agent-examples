import json
import requests
import csv
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter
from examples.util import anthropic_llm_call

def scrape_techcrunch_funding():
    """
    Scrapes TechCrunch for funding announcements from the last ~30 days.
    Returns a list of lead dictionaries:
        {
            "company_name": str,
            "funding_round": str,
            "funding_amount": float,
            "announcement_date": datetime,
            "company_url": str,
            "article_url": str
        }
    """
    leads = []
    base_url = "https://techcrunch.com/tag/funding/"
    response = requests.get(base_url)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    # Example parsing - TechCrunch layout changes frequently, so this is purely illustrative
    article_blocks = soup.find_all("div", class_="post-block")
    
    for block in article_blocks:
        # Extract article URL
        link_tag = block.find("a", class_="post-block__title__link")
        if not link_tag:
            continue
        article_url = link_tag["href"]
        
        # Extract article date
        time_tag = block.find("time")
        if time_tag and time_tag.has_attr("datetime"):
            announcement_date_str = time_tag["datetime"]
        else:
            announcement_date_str = datetime.now().isoformat()
        
        # Convert article date to datetime object
        announcement_date = datetime.fromisoformat(announcement_date_str.replace("Z", ""))
        
        # We’ll do a minimal check to see if it’s within 30 days
        days_ago_30 = datetime.now() - timedelta(days=30)
        if announcement_date < days_ago_30:
            continue

        # As a placeholder, we’ll guess the round and amount from text (not robust!)
        # In a real scenario, you'd parse the article content or snippet carefully.
        snippet = block.find("div", class_="post-block__content")
        snippet_text = snippet.get_text(strip=True) if snippet else ""
        
        # Simple naive checks to mimic extracting round/amount
        # Real-world usage: more sophisticated text extraction & NER
        round_type = "Seed" if "Seed" in snippet_text else \
                     "Series A" if "Series A" in snippet_text else \
                     "Series B" if "Series B" in snippet_text else "Unknown"
        
        # Minimal attempt to find an amount: look for '$xx million' or '$xxM'
        funding_amount = 0.0
        import re
        match = re.search(r"\$(\d+(\.\d+)?)\s*(million|M)", snippet_text, re.IGNORECASE)
        if match:
            # E.g. $5 million => 5, $2.5M => 2.5
            raw_amount = float(match.group(1))
            # Convert "X million" or "X M" to numeric
            funding_amount = raw_amount * 1_000_000
        
        # For company name, we might guess from the title
        company_name = link_tag.get_text(strip=True)
        # We can parse out extra text if the title is "Startup Foo raises..."
        # For demonstration, we’ll keep the entire title as the company_name field.

        # For a company URL, we’d typically have to parse the article itself.
        # We'll just leave it blank or guess.
        company_url = ""

        # Build the lead
        lead = {
            "company_name": company_name,
            "funding_round": round_type,
            "funding_amount": funding_amount,
            "announcement_date": announcement_date,
            "company_url": company_url,
            "article_url": article_url
        }
        leads.append(lead)
    return leads

def filter_leads(leads):
    """
    Filters leads based on:
      - Funding in last 30 days
      - Funding amount > $1M
      - Round type: Seed, Series A, or Series B
    """
    valid_rounds = {"Seed", "Series A", "Series B"}
    cutoff_date = datetime.now() - timedelta(days=30)
    filtered = []
    for lead in leads:
        if (lead["announcement_date"] >= cutoff_date and
            lead["funding_amount"] > 1_000_000 and
            lead["funding_round"] in valid_rounds):
            filtered.append(lead)
    return filtered

def save_leads(leads):
    """
    Saves leads to a CSV with a timestamp, and also to a JSON backup of raw data.
    """
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"funded_leads_{now_str}.csv"
    json_filename = f"funded_leads_{now_str}.json"
    
    # CSV
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["company_name", "funding_round", "funding_amount", 
                         "announcement_date", "company_url", "article_url"])
        for lead in leads:
            writer.writerow([
                lead["company_name"],
                lead["funding_round"],
                lead["funding_amount"],
                lead["announcement_date"].isoformat(),
                lead["company_url"],
                lead["article_url"]
            ])
    
    # JSON
    with open(json_filename, "w", encoding="utf-8") as jfile:
        json.dump(leads, jfile, default=str, indent=2)

    print(f"Saved {len(leads)} leads to {csv_filename} and {json_filename}")

# Now we integrate with the agent-style framework you provided.
toolbox = Toolbox()

# Let's add a tool to scrape TechCrunch funding
def scrape_funding_tool():
    """
    Scrape TechCrunch for the latest funding news and filter them.
    Returns a short text summary plus instructions for the next step.
    """
    raw_leads = scrape_techcrunch_funding()
    filtered = filter_leads(raw_leads)
    save_leads(filtered)  # This writes CSV & JSON
    if not filtered:
        return "No funding leads found matching criteria in the last 30 days."
    summary = [f"{idx+1}. {lead['company_name']} - {lead['funding_round']} - ${lead['funding_amount']}"
               for idx, lead in enumerate(filtered)]
    return "Found leads:\n" + "\n".join(summary)

toolbox.add_tool(
    name="scrape_funding",
    fn=scrape_funding_tool,
    args={},
    description="Scrape TechCrunch for new funding announcements and filter them."
)

parser = XMLParser(tag="tool")
formatter = XMLPromptFormatter(tag="tool")

# For demonstration, we pretend we have a conversation loop:
def run_agent():
    feedback_history = []
    query = "Find recently funded startups"

    for cycle in range(1):
        print(f"=== CYCLE {cycle + 1} ===")

        last_feedback = feedback_history[-1] if feedback_history else ""
        user_prompt = f"{last_feedback}\nCap, please: {query}"
        print("User prompt:\n", user_prompt, "\n")

        # Craft system prompt with usage instructions for the tools
        system_prompt = (
            "You are an assistant that can scrape TechCrunch funding to find leads.\n\n"
            + formatter.usage_prompt(toolbox)
        )
        # We'll do a minimal call to our example 'anthropic_llm_call' function
        # to see if the LLM decides to call any tools.
        # In practice, you'd provide your own LLM prompt to instruct usage.
        response = anthropic_llm_call(
            system_prompt=system_prompt,
            prompt=(
                user_prompt + "\n\n"
                "Suggest how to find relevant funding leads, and call a tool if necessary."
            )
        )
        print("LLM response:\n", response, "\n")

        # Parse out any <tool> usage
        events = parser.parse(response)
        for event in events:
            if event.is_tool_call:
                tool_response = toolbox.use(event)
                if tool_response:
                    feedback_history.append(tool_response.result)
                    print("Tool output:\n", tool_response.result, "\n")

    print("=== FINAL FEEDBACK ACROSS ALL CYCLES ===\n")
    for i, fb in enumerate(feedback_history, start=1):
        print(f"Cycle {i} feedback:\n{fb}\n---\n")

if __name__ == "__main__":
    run_agent()
