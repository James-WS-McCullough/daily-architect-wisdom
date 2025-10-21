#!/usr/bin/env python3
"""
Fetch and parse all 97 articles from "97 Things Every Software Architect Should Know"
"""

import json
import re
import time
from urllib.request import urlopen, Request
from html.parser import HTMLParser
from typing import List, Dict

class ArticleParser(HTMLParser):
    """Parse HTML article to extract title, author, and content."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.author = ""
        self.content_parts = []
        self.in_h1 = False
        self.in_h2 = False
        self.in_p = False
        self.in_article = False
        self.in_footer = False
        self.in_author_p = False
        self.current_text = ""
        self.current_p_class = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'h1':
            self.in_h1 = True
        elif tag == 'h2':
            self.in_h2 = True
        elif tag == 'p':
            self.in_p = True
            self.current_p_class = attrs_dict.get('class', None)
            if self.current_p_class == 'author':
                self.in_author_p = True
        elif tag == 'article':
            self.in_article = True
        elif tag == 'footer':
            self.in_footer = True

    def handle_endtag(self, tag):
        if tag == 'h1':
            self.in_h1 = False
        elif tag == 'h2':
            self.in_h2 = False
        elif tag == 'p':
            self.in_p = False
            # Only add to content if it's not an author paragraph and not in footer
            if self.current_text.strip() and not self.in_author_p and not self.in_footer:
                self.content_parts.append(self.current_text.strip())
            self.current_text = ""
            self.current_p_class = None
            self.in_author_p = False
        elif tag == 'article':
            self.in_article = False
        elif tag == 'footer':
            self.in_footer = False

    def handle_data(self, data):
        text = data.strip()
        if not text:
            # Still need to preserve spaces in paragraph content
            if self.in_p and not self.in_author_p:
                self.current_text += data
            return

        # Capture title (from h1)
        if self.in_h1 and not self.title:
            self.title = text

        # Capture subtitle/author (from h2)
        elif self.in_h2:
            if not self.title:
                self.title = text

        # Capture author from <p class="author">
        elif self.in_author_p:
            if text.lower().startswith('by '):
                self.author = text[3:].strip()
            else:
                self.author = text

        # Capture content (from p tags not in footer)
        elif self.in_p and not self.in_footer:
            self.current_text += data

    def get_content(self):
        """Return the full content with paragraphs separated by double newlines."""
        return "\n\n".join(self.content_parts)


def fetch_article(filename: str) -> Dict[str, str]:
    """Fetch and parse a single article."""
    base_url = "https://yoshi389111.github.io/kinokobooks/soft_en/"
    url = base_url + filename

    print(f"Fetching: {filename}")

    try:
        # Add headers to avoid being blocked
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')

        # Parse the HTML
        parser = ArticleParser()
        parser.feed(html)

        # Extract title, author, and content
        title = parser.title
        author = parser.author
        content = parser.get_content()

        # Fallback: if parser didn't find content, try alternative extraction
        if not content:
            # Try to extract from article/div/body tags
            content = extract_text_fallback(html)

        # Clean up title - remove special characters encoding issues
        title = title.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

        return {
            "title": title,
            "author": author,
            "content": content
        }

    except Exception as e:
        print(f"Error fetching {filename}: {e}")
        return {
            "title": f"Error: {filename}",
            "author": "Unknown",
            "content": f"Failed to fetch article: {e}"
        }


def extract_text_fallback(html: str) -> str:
    """Fallback method to extract text content from HTML."""
    # Remove script and style tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Extract paragraphs
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, flags=re.DOTALL)

    # Clean up HTML tags and entities
    text_parts = []
    for p in paragraphs:
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', p)
        # Decode HTML entities
        text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        text = text.replace('&quot;', '"').replace('&#39;', "'")
        text = text.strip()
        if text:
            text_parts.append(text)

    return "\n\n".join(text_parts)


def main():
    """Main function to fetch all articles."""

    # List of all 97 article filenames
    filenames = [
        "Dont_put_your_resume_ahead_of_the_requirements.htm",
        "Simplify_essential_complexity;_diminish_accidental_complexity.htm",
        "Chances_are_your_biggest_problem_isnt_technical.htm",
        "Communication_is_King;_Clarity_and_Leadership_its_humble_servants.htm",
        "Application_architecture_determines_application_performance.htm",
        "Seek_the_value_in_requested_capabilities.htm",
        "Stand_Up.htm",
        "Everything_will_ultimately_fail.htm",
        "Youre_negotiating_more_often_than_you_think..htm",
        "Quantify.htm",
        "One_line_of_working_code_is_worth_500_of_specification.htm",
        "There_is_no_one-size-fits-all_solution.htm",
        "Its_never_too_early_to_think_about_performance.htm",
        "Architecting_is_about_balancing.htm",
        "Commit-and-run_is_a_crime..htm",
        "There_Can_be_More_than_One.htm",
        "Business_Drives.htm",
        "Simplicity_before_generality,_use_before_reuse.htm",
        "Architects_must_be_hands_on.htm",
        "Continuously_Integrate.htm",
        "Avoid_Scheduling_Failures.htm",
        "Architectural_Tradeoffs.htm",
        "Database_as_a_Fortress.htm",
        "Use_uncertainty_as_a_driver.htm",
        "Warning,_problems_in_mirror_may_be_larger_than_they_appear.htm",
        "Reuse_is_about_people_and_education,_not_just_architecture.htm",
        "There_is_no_I_in_architecture.htm",
        "Get_the_1000ft_view.htm",
        "Try_before_choosing.htm",
        "Understand_The_Business_Domain.htm",
        "Programming_is_an_act_of_design.htm",
        "Give_developers_autonomy.htm",
        "Time_changes_everything.htm",
        "The_title_of_software_architect_has_only_lower-case_as_deal_with_it.htm",
        "Scope_is_the_enemy_of_success.htm",
        "Value_stewardship_over_showmanship.htm",
        "Software_architecture_has_ethical_consequences.htm",
        "Skyscrapers_arent_scalable.htm",
        "Heterogeneity_Wins.htm",
        "Its_all_about_performance.htm",
        "Engineer_in_the_white_spaces.htm",
        "Talk_the_Talk.htm",
        "Context_is_King.htm",
        "Dwarves,_Elves,_Wizards,_and_Kings.htm",
        "Learn_from_Architects_of_Buildings.htm",
        "Fight_repetition.htm",
        "Welcome_to_the_Real_World.htm",
        "Dont_Control,_but_Observe.htm",
        "Janus_the_Architect.htm",
        "Architects_focus_is_on_the_boundaries_and_interfaces.htm",
        "Empower_developers.htm",
        "Record_your_rationale.htm",
        "Challenge_assumptions_-_especially_your_own.htm",
        "Share_your_knowledge_and_experiences.htm",
        "Pattern_Pathology.htm",
        "Dont_Stretch_The_Architecture_Metaphors.htm",
        "Focus_on_Application_Support_and_Maintenance.htm",
        "Prepare_to_pick_two.htm",
        "Prefer_principles,_axioms_and_analogies_to_opinion_and_taste.htm",
        "Start_with_a_Walking_Skeleton.htm",
        "It_is_all_about_the_data.htm",
        "Make_sure_the_simple_stuff_is_simple.htm",
        "Before_anything,_an_architect_is_a_developer.htm",
        "The_ROI_variable.htm",
        "Your_system_is_legacy,_design_for_it..htm",
        "If_there_is_only_one_solution,_get_a_second_opinion.htm",
        "Understand_the_impact_of_change.htm",
        "You_have_to_understand_Hardware_too.htm",
        "Shortcuts_now_are_paid_back_with_interest_later.htm",
        "Perfect_is_the_Enemy_of_Good_Enough.htm",
        "Avoid_Good_Ideas.htm",
        "Great_content_creates_great_systems.htm",
        "The_Business_Vs._The_Angry_Architect.htm",
        "Stretch_key_dimensions_to_see_what_breaks.htm",
        "If_you_design_it,_you_should_be_able_to_code_it..htm",
        "A_rose_by_any_other_name_will_end_up_as_a_cabbage.htm",
        "Stable_problems_get_high_quality_solutions.htm",
        "It_Takes_Diligence.htm",
        "Take_responsibility_for_your_decisions.htm",
        "Dont_Be_Clever.htm",
        "Choose_your_weapons_carefully,_relinquish_them_reluctantly.htm",
        "Your_Customer_is_Not_Your_Customer.htm",
        "It_will_never_look_like_that.htm",
        "Choose_Frameworks_that_play_well_with_others.htm",
        "Make_a_strong_business_case.htm",
        "Control_the_data,_not_just_the_code.htm",
        "Pay_down_your_technical_debt.htm",
        "Dont_Be_a_Problem_Solver.htm",
        "Build_Systems_to_be_Zuhanden.htm",
        "Find_and_retain_passionate_problem_solvers.htm",
        "Software_doesnt_really_exist.htm",
        "Learn_a_new_language.htm",
        "You_cant_future-proof_solutions.htm",
        "The_User_Acceptance_Problem.htm",
        "The_Importance_of_Consomme.htm",
        "For_the_end-user,_the_interface_is_the_system.htm",
        "Great_software_is_not_built,_it_is_grown.htm"
    ]

    articles = []

    for i, filename in enumerate(filenames, 1):
        print(f"\n[{i}/97] Processing: {filename}")
        article = fetch_article(filename)
        articles.append(article)

        # Be polite to the server - small delay between requests
        if i < len(filenames):
            time.sleep(0.5)

    # Create the final JSON structure
    output = {
        "inspiration": articles
    }

    # Write to file
    output_path = "/Users/jamesmccullough/Documents/Github/daily-architect-wisdom/parsed_articles.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n\nSuccessfully parsed {len(articles)} articles!")
    print(f"Output written to: {output_path}")

    # Print summary
    print("\n=== Summary ===")
    for i, article in enumerate(articles[:5], 1):
        print(f"{i}. {article['title']} by {article['author']}")
    print(f"... and {len(articles) - 5} more articles")


if __name__ == "__main__":
    main()
