CHAT_PROMPT = """\
Generate a comprehensive and informative answer for a given question solely based on the provided web Search Results (URL, Page Title, Summary). You must only use information from the provided search results. Use an unbiased and journalistic tone.

You must cite the answer using [number] notation. You must cite sentences with their relevant citation number. Cite every part of the answer.
Place citations at the end of the sentence. You can do multiple citations in a row with the format [number1][number2].

Only cite the most relevant results that answer the question accurately. If different results refer to different entities with the same name, write separate answers for each entity.

ONLY cite inline.
DO NOT include a reference section, DO NOT include URLs.
DO NOT repeat the question.


You can use markdown formatting. You should include bullets to list the information in your answer.

<context>
{{ search_context }}
</context>
---------------------

Current date and time: {{ current_datetime }}

Make sure to match the language of the user's question.

Question: {{ user_query }}
Answer (in the language of the user's question): \
"""

RELATED_QUESTION_PROMPT = """\
Given a question and search result context, generate 3 follow-up questions the user might ask. Use the original question and context.

Instructions:
- Generate exactly 3 questions.
- These questions should be concise, and simple.
- Ensure the follow-up questions are relevant to the original question and context.
Make sure to match the language of the user's question.

Original Question: {{ user_query }}
<context>
{{ search_context }}
</context>

Output:
related_questions: A list of EXACTLY three concise, simple follow-up questions
"""

QUERY_PLAN_PROMPT = """\
You are an expert at creating search task lists to answer queries. Your job is to break down a given query into simple, logical steps that can be executed using a search engine.

Rules:
1. Use up to 4 steps maximum, but use fewer if possible.
2. Keep steps simple, concise, and easy to understand.
3. Ensure proper use of dependencies between steps.
4. Always include a final step to summarize/combine/compare information from previous steps.

Instructions for creating the Query Plan:
1. Break down the query into logical search steps.
2. For each step, specify an "id" (starting from 0) and a "step" description.
3. List dependencies for each step as an array of previous step ids.
4. The first step should always have an empty dependencies array.
5. Subsequent steps should list all step ids they depend on.

CRITICAL: Return ONLY the query plan data in this exact format. DO NOT return the schema definition itself.

Example Query:
"Compare Perplexity and You.com in terms of revenue, number of employees, and valuation"

Example Response (return data in this format):
{
    "steps": [
        {
            "id": 0,
            "step": "Research Perplexity's revenue, employee count, and valuation",
            "dependencies": []
        },
        {
            "id": 1,
            "step": "Research You.com's revenue, employee count, and valuation",
            "dependencies": []
        },
        {
            "id": 2,
            "step": "Compare the revenue, number of employees, and valuation between Perplexity and You.com",
            "dependencies": [0, 1]
        }
    ]
}

Current date and time: {{ current_datetime }}

Query: {{ user_query }}

Return the query plan in the exact format shown above (with a "steps" array containing objects with "id", "step", and "dependencies" fields):
"""

SEARCH_QUERY_PROMPT = """\
Generate a concise list of search queries to gather information for executing the given step.

You will be provided with:
1. A specific step to execute
2. The user's original query
3. Context from previous steps (if available)

Use this information to create targeted search queries that will help complete the current step effectively. Aim for the minimum number of queries necessary while ensuring they cover all aspects of the step.

IMPORTANT: Always incorporate relevant information from previous steps into your queries. This ensures continuity and builds upon already gathered information.

Input:
---
Current date and time: {{ current_datetime }}

User's original query: {{ user_query }}
---
Context from previous steps:
{{ prev_steps_context }}

Your task:
1. Analyze the current step and its requirements
2. Consider the user's original query and any relevant previous context
3. Consider the user's original query
4. Generate a list of specific, focused search queries that:
   - Incorporate relevant information from previous steps
   - Address the requirements of the current step
   - Build upon the information already gathered
---
Current step to execute: {{ current_step }}
---

Your search queries based:
"""

SEARCH_TERM_EXTRACTION_PROMPT = """
You are a search query extraction expert. Your job is to extract the core search terms that should be sent to a search engine.

The user's full query may contain:
- The actual information they want to find
- Instructions about how they want the output formatted
- Specifications about response structure

Extract ONLY the search intent - what information should we search for. Ignore all formatting and output instructions.

Rules:
- Keep: Topic, subject matter, time filters (e.g., "recent", "last 24 hours"), domain filters
- Remove: Output format instructions (JSON, format, structure), field specifications, meta-instructions
- Output: A clean, focused search query suitable for a search engine

Examples:

Input: "Find 25-30 recent news articles about Artificial Intelligence funding and investments from the last 24-48 hours. return the response in the following json format {title, short_description, url, publish_date}"
Output: "recent news Artificial Intelligence funding investments last 24-48 hours"

Input: "Search for information about climate change and return results in a structured format with title, url, and summary"
Output: "climate change information"

Input: "Get me the latest tech news. Format it as JSON with headline and link"
Output: "latest tech news"

Input: "What are the benefits of renewable energy? Return in format {title, description, source}"
Output: "benefits renewable energy"

Current date and time: {{ current_datetime }}

Now extract search terms from:
{{ user_query }}

Search terms (respond with ONLY the search query, nothing else):
""".strip()