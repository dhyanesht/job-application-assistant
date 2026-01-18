from bs4 import BeautifulSoup
import re

def parse_job_page(html: str) -> dict:
    """Parse Dice job detail page HTML and return structured job data."""
    soup = BeautifulSoup(html, "lxml")

    # --- Job Title ---
    job_title = "Not Available"
    summary_div = None  # define upfront

    # Old method: <h1> tag
    h1 = soup.find("h1")
    if h1:
        job_title = h1.text.strip()
    else:
        # New method: look in summary text for <b> job title pattern
        summary_div = soup.find("div", class_=lambda x: x and "job-detail-description-module" in x)
        if summary_div:
            match = re.search(r"searching for a <b>(.*?)</b>", str(summary_div), re.IGNORECASE)
            if match:
                job_title = match.group(1).strip()

    # --- Company Name & Link ---
    company_name = "Not Available"
    company_link = "Not Available"
    # try <a> first
    company_a = soup.find("a", href=True)
    if company_a:
        company_name = company_a.text.strip()
        company_link = company_a["href"].strip()
    else:
        # fallback: look for <li> or <p> containing company info
        company_p = soup.find(string=re.compile(r"Company", re.IGNORECASE))
        if company_p:
            company_name = company_p.strip()

    # --- Location ---
    location = "Not Available"
    # Old method: <li> containing comma
    loc_li = soup.find("li", string=lambda x: x and "," in x)
    if loc_li:
        location = loc_li.text.strip()
    else:
        # New method: inside summary text, look for 'in <City, ST>'
        if summary_div:
            match = re.search(r"in\s+([A-Za-z ,]+)</b>", str(summary_div))
            if match:
                location = match.group(1).strip()

    # --- Posted Date ---
    posted_date = "Not Available"
    posted_li = soup.find("li", string=lambda x: x and "Posted" in x)
    if posted_li:
        posted_date = posted_li.text.strip()

    # --- Job Overview ---
    overview_details = get_job_overview(soup)

    # --- Recruiter Info ---
    recruiter_info = recruiter_details(soup)

    # --- Merge all info ---
    job_data = {
        "Job Title": job_title,
        "Company Name": company_name,
        "Company Link": company_link,
        "Location": location,
        "Posted Date": posted_date,
    }
    job_data.update(overview_details)
    job_data.update(recruiter_info)

    return job_data


def get_job_overview(soup):
    details = {}

    # --- Employment / Pay / Work Arrangement / Travel ---
    for container in soup.find_all("div", class_=lambda x: x and "job-overview_detailContainer" in x):
        for chip in container.find_all("div", class_=lambda x: x and "chip_chip" in x):
            text = chip.text.strip()
            if "Contract" in text:
                details["Employment Type"] = text
            elif "$" in text:
                details["Pay"] = text
            elif "Hybrid" in text or "days" in text:
                details["Work Arrangement"] = text
            elif "Travel" in text:
                details["Travel Requirements"] = text

    # --- Skills ---
    skills = []
    # New structure: <h3>Skills</h3> followed by <ul><li>...
    skills_h3 = soup.find("h3", string=lambda x: x and "Skills" in x)
    if skills_h3:
        ul = skills_h3.find_next_sibling("ul")
        if ul:
            for li in ul.find_all("li"):
                div = li.find("div", class_=lambda x: x and "font-medium" in x)
                if div:
                    skills.append(div.text.strip())
    details["Primary Skill Set"] = skills

    # --- Job Description ---
    job_desc = soup.find("div", class_=lambda x: x and "job-detail-description-module" in x)
    if job_desc:
        details["Job Description"] = job_desc.get_text(separator="\n").strip()
    else:
        details["Job Description"] = "Not Available"

    return details


def recruiter_details(soup):
    recruiter_section = soup.find("div", {"data-cy": "recruiterProfileWidget"})
    if recruiter_section:
        name_el = recruiter_section.find("p", {"data-cy": "recruiterName"})
        company_el = recruiter_section.find("p", {"data-cy": "recruiterCompany"})
        return {
            "Recruiter Name": name_el.text.strip() if name_el else "Not Available",
            "Recruiter Company": company_el.text.strip() if company_el else "Not Available",
        }
    return {"Recruiter Name": "Not Available", "Recruiter Company": "Not Available"}
