import feedparser
from datetime import datetime, timedelta, timezone
import json
import requests
import os
import openai

# Example PubMed RSS feed URL
rss_url = 'https://pubmed.ncbi.nlm.nih.gov/rss/search/12cYCaYYmd3PKH1TcODuh5Cr7776fWscbUhYnAwoSRATXNoE-E/?limit=100&utm_campaign=pubmed-2&fc=20250204112327'

access_token = os.getenv('GITHUB_TOKEN')
openaiapikey = os.getenv('OPENAI_API_KEY')

client = openai.OpenAI(api_key=openaiapikey)

def extract_scores(text):
    # Use OpenAI API to get Research Score and Social Impact Score separately
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an environmental science expert and researcher. You are skilled at selecting interesting/novelty research."},
            {"role": "user", "content": f"Given the text '{text}', evaluate this article with two scores:\n"
                                        "1. Research Score (0-100): Based on research innovation, methodological rigor, and data reliability.\n"
                                        "2. Social Impact Score (0-100): Based on public attention, policy relevance, and societal impact.\n"
                                        "Provide the scores in the following format:\n"
                                        "Research Score: <score>\n"
                                        "Social Impact Score: <score>"}
        ],
        max_tokens=100,
        temperature=0.5
    )

    generated_text = response.choices[0].message.content.strip()  

    # Extract research score
    research_score_start = generated_text.find("Research Score:")
    research_score = generated_text[research_score_start+len("Research Score:"):].split("\n")[0].strip()

    # Extract social impact score
    social_impact_score_start = generated_text.find("Social Impact Score:")
    social_impact_score = generated_text[social_impact_score_start+len("Social Impact Score:"):].strip()

    return research_score, social_impact_score

def get_pubmed_abstracts(rss_url):
    abstracts_with_urls = []

    # Parse the PubMed RSS feed
    feed = feedparser.parse(rss_url)

    # Calculate the date one week ago
    one_week_ago = datetime.now(timezone.utc) - timedelta(weeks=1)

    # Iterate over entries in the PubMed RSS feed and extract abstracts and URLs
    for entry in feed.entries:
        # Get the publication date of the entry
        published_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')

        # If the publication date is within one week, extract the abstract and URL
        if published_date >= one_week_ago:
            # Get the abstract and DOI of the entry
            title = entry.title
            abstract = entry.content[0].value
            doi = entry.dc_identifier
            abstracts_with_urls.append({"title": title, "abstract": abstract, "doi": doi})

    return abstracts_with_urls

# Get the abstracts from the PubMed RSS feed
pubmed_abstracts = get_pubmed_abstracts(rss_url)

# Create an empty list to store each abstract with its scores
new_articles_data = []

for abstract_data in pubmed_abstracts:
    title = abstract_data["title"]
    research_score, social_impact_score = extract_scores(abstract_data["abstract"])
    doi = abstract_data["doi"]

    new_articles_data.append({
        "title": title,
        "research_score": research_score,
        "social_impact_score": social_impact_score,
        "doi": doi
    })
    
# Create issue title and content
issue_title = f"Weekly Article Matching - {datetime.now().strftime('%Y-%m-%d')}"
issue_body = "Below are the article matching results from the past week:\n\n"

for article_data in new_articles_data:
    abstract = article_data["title"]
    research_score = article_data["research_score"]
    social_impact_score = article_data["social_impact_score"]
    doi = article_data.get("doi", "No DOI available")  # Default to "No DOI available" if DOI field is missing

    issue_body += f"- **Title**: {abstract}\n"
    issue_body += f"  **Research Score**: {research_score}\n"
    issue_body += f"  **Social Impact Score**: {social_impact_score}\n"
    issue_body += f"  **DOI**: {doi}\n\n"

def create_github_issue(title, body, access_token):
    url = f"https://api.github.com/repos/yufree/hjhbb/issues"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "title": title,
        "body": body
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 201:
        print("Issue created successfully!")
    else:
        print("Failed to create issue. Status code:", response.status_code)
        print("Response:", response.text)

# Create the issue
create_github_issue(issue_title, issue_body, access_token)
