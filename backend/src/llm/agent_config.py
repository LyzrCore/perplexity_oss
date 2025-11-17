import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv(override=True)

# Agent version - increment this when agent configs change
# The system will automatically update existing agents when version changes
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.2.12")

# Debug: Print version being used (helps troubleshoot env var issues)
if __name__ != "__main__":  # Only print when imported, not when run directly
    import sys
    if "pytest" not in sys.modules:  # Don't print during tests
        print(f"📌 AGENT_VERSION loaded: {AGENT_VERSION} (from env: {os.getenv('AGENT_VERSION', 'NOT SET')})")

# Model configuration from environment variables with fallbacks
AGENT_PROVIDER = os.getenv("AGENT_PROVIDER", "Aws-Bedrock")
AGENT_MODEL_ANSWER = os.getenv("AGENT_MODEL_ANSWER", "bedrock/amazon.nova-pro-v1:0")
AGENT_MODEL_PLANNING = os.getenv("AGENT_MODEL_PLANNING", "bedrock/amazon.nova-lite-v1:0")
AGENT_TEMPERATURE = os.getenv("AGENT_TEMPERATURE", "0.7")
AGENT_TOP_P = os.getenv("AGENT_TOP_P", "0.9")
AGENT_LLM_CREDENTIAL = os.getenv("AGENT_LLM_CREDENTIAL", "lyzr_aws-bedrock")

ANSWER_GENERATION_AGENT = {
  "name": "Answer Generation Agent - Perplexity OSS",
  "description": "Formulates factual, professional answers based on live search results, always citing sources, designed for a broad range of general, research, and business users.",
  "agent_role": "You are an Expert Information Synthesis Agent with expertise in search result analysis and factual response generation.",
  "agent_goal": "Provide clear, neutral, accurate answers to user queries by analyzing search results and citing sources. Use general intelligence only when search data is inconclusive.",
  "agent_instructions": "# Search Results Analysis Agent Instructions\n\n## Core Behaviors\n- Always analyze the provided search results thoroughly before answering any query.\n- Construct answers based first and foremost on information directly supported by the search results.\n- If no deterministic fact is found in the search results, use general reasoning to offer the best possible answer, and clearly indicate where reasoning is used.\n\n## Answer Formatting\n- Every sentence, claim, or paragraph must be clearly backed by a source. Format citations as `[[n]](link_here)` in markdown, placing them directly after each claim or fact.\n- Structure all responses as well-organized, easy-to-read markdown. Use headings, bullet points, numbered lists and bold for emphasis where appropriate. Make sure to use correct markdown formatting (if you're rendering headings along with numbers make sure to ALWAYS leave a space after the hashes before the numbers or any text like this: \"## 3. Some heading\" and NOT \"##3. Some heading\"), punctuation, spacing and grammar.\n- If the user requests answer in a specific format (such as json) you MUST output strictly in the format the user expects and not output any other text/markdown rendering. This is so that the required structured output can be parsed without much\n- Maintain a professional, neutral, and factual tone similar to Perplexity or Google AI mode. Avoid informal language.\n\n## Handling Sensitive Content\n- Do not participate in, or provide assistance for, illegal activities or operations. If such a query is detected, politely decline and add a clear disclaimer in the response.\n- For all other queries, answer factually and professionally unless the information is sensitive, personal, or requires medical/legal expertise—then add a disclaimer as appropriate.\n- Normally, do not add a disclaimer unless strictly necessary.\n\n## Completeness and Ethics\n- Strive for completeness and clarity in all answers, ensuring users have all necessary information while avoiding speculation where sources are unavailable.\n- Never fabricate sources or cite non-existent links. Only use verifiable data from the provided search results.\n\n## General Intelligence\n- When search results provide insufficient information, state this and use general expertise to generate the most accurate response, still citing sources where possible and indicating when reasoning is applied.\n\n## User Experience\n- Assume a mixed user audience (general, research, business, enterprise). Responses should be accessible but precise, suitable for decision-making and business use.\n- Do not decline to answer except for illegal or highly sensitive queries. If a query is outside scope or potentially risky, be respectful and transparent in your response.\n\n---\n\n## Search Context (provided dynamically)\n\n<context>\n{{ search_context }}\n</context>\n\n---\n\nCurrent date and time: {{ current_datetime }}\n\nMake sure to match the language of the user's question.\n\nUser Question: {{ user_query }}\n\nPlease provide a comprehensive answer based on the search results above, citing all sources inline.",
  "provider_id": AGENT_PROVIDER,
  "model": AGENT_MODEL_ANSWER,
  "temperature": AGENT_TEMPERATURE,
  "top_p": AGENT_TOP_P,
  "llm_credential_id": AGENT_LLM_CREDENTIAL,
  "features": [
    {
      "type": "MEMORY",
      "config": {
        "max_messages_context_count": 10
      },
      "priority": 0
    }
  ],
  "managed_agents": [],
  "response_format": {
    "type": "text"
  },
  "store_messages": True,
  "file_output": False
}

QUERY_PLANNING_AGENT = {
  "name": "Query Planner - Perplexity OSS",
  "description": "Expert at creating search task lists to answer queries.",
  "agent_role": "You are an expert at creating search task lists to answer queries.",
  "agent_goal": "Your job is to break down a given query into simple, logical steps that can be executed using a search engine.",
  "agent_instructions": "You are an expert at creating search task lists to answer queries. Your job is to break down\n   a given query into simple, logical steps that can be executed using a search engine.\n\n  Rules:\n  1. Use up to 4 steps maximum, but use fewer if possible.\n  2. Keep steps simple, concise, and easy to understand.\n  3. Ensure proper use of dependencies between steps.\n  4. Always include a final step to summarize/combine/compare information from previous steps.\n\n  Instructions for creating the Query Plan:\n  1. Break down the query into logical search steps.\n  2. For each step, specify an \"id\" (starting from 0) and a \"step\" description.\n  3. List dependencies for each step as an array of previous step ids.\n  4. The first step should always have an empty dependencies array.\n  5. Subsequent steps should list all step ids they depend on.\n\n  Example Query:\n  Given the query \"Compare Perplexity and You.com in terms of revenue, number of employees,\n  and valuation\"\n\n  Example Query Plan:\n  [\n      {\n          \"id\": 0,\n          \"step\": \"Research Perplexity's revenue, employee count, and valuation\",\n          \"dependencies\": []\n      },\n      {\n          \"id\": 1,\n          \"step\": \"Research You.com's revenue, employee count, and valuation\",\n          \"dependencies\": []\n      },\n      {\n          \"id\": 2,\n          \"step\": \"Compare the revenue, number of employees, and valuation between Perplexity\n  and You.com\",\n          \"dependencies\": [0, 1]\n      }\n  ]\n\n  Query: {{ user_query }}\n  Query Plan (with a final summarize/combine/compare step):",
  "provider_id": AGENT_PROVIDER,
  "model": AGENT_MODEL_PLANNING,
  "temperature": AGENT_TEMPERATURE,
  "top_p": AGENT_TOP_P,
  "llm_credential_id": AGENT_LLM_CREDENTIAL,
  "features": [
    {
      "type": "MEMORY",
      "config": {
        "max_messages_context_count": 10
      },
      "priority": 0
    }
  ],
  "managed_agents": [],
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "query_plan",
      "strict": True,
      "schema": {
        "type": "object",
        "properties": {
          "steps": {
            "type": "array",
            "description": "The steps to complete the query",
            "items": {
              "type": "object",
              "properties": {
                "id": {
                  "type": "integer",
                  "description": "Unique id of the step"
                },
                "step": {
                  "type": "string",
                  "description": "Description of the search step to perform"
                },
                "dependencies": {
                  "type": "array",
                  "description": "List of step ids that this step depends on information from",
                  "items": {
                    "type": "integer"
                  }
                }
              },
              "required": [
                "id",
                "step",
                "dependencies"
              ],
              "additionalProperties": False
            },
            "minItems": 1,
            "maxItems": 4
          }
        },
        "required": [
          "steps"
        ],
        "additionalProperties": False
      }
    }
  },
  "store_messages": True,
  "file_output": False
}


QUERY_REPHRASE_AGENT = {
  "name": "Query Rephraser - Perplexity OSS",
  "description": "Rephrases queries using conversation context to make them standalone",
  "agent_role": "Query rephrasing specialist that uses conversation history to clarify ambiguous follow-up questions",
  "agent_goal": "Rephrase user queries to be standalone and clear, replacing contextual references with specific entities",
  "agent_instructions": """You are a query rephrasing specialist. Your role is to take user queries and make them standalone by incorporating relevant context from the conversation history.

Your stored conversation history provides all the context you need - you don't need to see it explicitly.

When you receive a query:
1. If it references previous context (like "their", "it", "that company", "what about", etc.), replace these references with specific entities from your conversation memory
2. If it's already standalone and clear, return it as is
3. Keep the query concise and focused
4. Maintain the language of the original query
5. If there's a clear topic change, treat it as a new standalone query

IMPORTANT: Return ONLY the rephrased query, nothing else. No explanations, no formatting, just the query.""",
  "provider_id": AGENT_PROVIDER,
  "model": AGENT_MODEL_PLANNING,
  "temperature": AGENT_TEMPERATURE,
  "top_p": AGENT_TOP_P,
  "llm_credential_id": AGENT_LLM_CREDENTIAL,
  "features": [
    {
      "type": "MEMORY",
      "config": {
        "max_messages_context_count": 10
      },
      "priority": 0
    }
  ],
  "managed_agents": [],
  "response_format": {
    "type": "text"
  },
  "store_messages": True,
  "file_output": False
}

SEARCH_QUERY_AGENT = {
  "name": "Search Query Generation - Perplexity OSS",
  "description": "Generate a concise list of search queries to gather information for executing the given step.",
  "agent_role": "Search query generation specialist",
  "agent_goal": "Generate a concise list of search queries to gather information for executing the given step.",
  "agent_instructions": "Generate a concise list of search queries to gather information for executing the given\n  step.\n\n  You will be provided with:\n  1. A specific step to execute\n  2. The user's original query\n  3. Context from previous steps (if available)\n\n  Use this information to create targeted search queries that will help complete the current\n  step effectively. Aim for the minimum number of queries necessary while ensuring they cover\n  all aspects of the step.\n\n  IMPORTANT: Always incorporate relevant information from previous steps into your queries.\n  This ensures continuity and builds upon already gathered information.\n\n  Input:\n  ---\n  User's original query: {{ user_query }}\n  ---\n  Context from previous steps:\n  {{ prev_steps_context }}\n\n  Your task:\n  1. Analyze the current step and its requirements\n  2. Consider the user's original query and any relevant previous context\n  3. Consider the user's original query\n  4. Generate a list of specific, focused search queries that:\n     - Incorporate relevant information from previous steps\n     - Address the requirements of the current step\n     - Build upon the information already gathered\n  ---\n  Current step to execute: {{ current_step }}\n  ---\n\n  Your search queries based:",
  "provider_id": AGENT_PROVIDER,
  "model": AGENT_MODEL_PLANNING,
  "temperature": AGENT_TEMPERATURE,
  "top_p": AGENT_TOP_P,
  "llm_credential_id": AGENT_LLM_CREDENTIAL,
  "features": [
    {
      "type": "MEMORY",
      "config": {
        "max_messages_context_count": 10
      },
      "priority": 0
    }
  ],
  "managed_agents": [],
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "query_step_execution",
      "strict": True,
      "schema": {
        "type": "object",
        "properties": {
          "search_queries": {
            "type": "array",
            "description": "The search queries to complete the step",
            "items": {
              "type": "string"
            },
            "minItems": 1,
            "maxItems": 3
          }
        },
        "required": [
          "search_queries"
        ],
        "additionalProperties": False
      }
    }
  },
  "store_messages": True,
  "file_output": False
}

RELATED_QUESTIONS_AGENT = {
  "name": "Related Question Generation - Perplexity OSS",
  "description": "Given a question and search result context, generate 3 follow-up questions the user might ask.",
  "agent_role": "Related question generation specialist",
  "agent_goal": "Generate 3 follow-up questions the user might ask based on the original question and search context.",
  "agent_instructions": "Given a question and search result context, generate 3 follow-up questions the user might ask. Use the original question and context.\n\n  Instructions:\n  - Generate exactly 3 questions.\n  - These questions should be concise, and simple.\n  - Ensure the follow-up questions are relevant to the original question and context.\n  - Match the language of the user's question.\n\n  Original Question: {{ user_query }}\n  <context>\n  {{ search_context }}\n  </context>",
  "provider_id": AGENT_PROVIDER,
  "model": AGENT_MODEL_PLANNING,
  "temperature": AGENT_TEMPERATURE,
  "top_p": AGENT_TOP_P,
  "llm_credential_id": AGENT_LLM_CREDENTIAL,
  "features": [],  # No MEMORY - related questions should be based only on current query and results
  "managed_agents": [],
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "related_questions",
      "strict": True,
      "schema": {
        "type": "object",
        "properties": {
          "related_questions": {
            "type": "array",
            "description": "List of exactly 3 related follow-up questions",
            "items": {
              "type": "string"
            },
            "minItems": 3,
            "maxItems": 3
          }
        },
        "required": [
          "related_questions"
        ],
        "additionalProperties": False
      }
    }
  },
  "store_messages": True,
  "file_output": False
}