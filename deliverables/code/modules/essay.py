import os
from openai import OpenAI
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec


# few-shot prompting proven to have better results
FEW_SHOT_EXAMPLES = [
    {
        "role": "system",
        "content": (
            "You are a literary scholar specializing in comparative literature. "
            "You produce 5-paragraph academic essays with a clear introduction, three detailed body paragraphs, "
            "and a strong conclusion. You always support your arguments with direct quotes, citing them in the format "
            "(filename, Page X) or (filename, Chapter Y)."
        )
    },
    {
        "role": "user",
        "content": "Analyze how 'Book A' addresses the theme of social isolation, including direct citations."
    },
    {
        "role": "assistant",
        "content": (
            "In 'Book A,' social isolation is portrayed as a profound internal struggle. For example, the protagonist states, "
            "\"I felt utterly cut off from the world,\" as seen in chunk 12 (BookA.pdf, Page 24). This direct quote underlines "
            "the personal anguish of isolation and sets the tone for the character’s emotional journey."
        )
    },
    {
        "role": "user",
        "content": "Compare how 'Book A' and 'Book B' treat social isolation."
    },
    {
        "role": "assistant",
        "content": (
            "When comparing 'Book A' and 'Book B,' a clear contrast emerges. 'Book A' uses introspective narrative to depict "
            "isolation—evidenced by the line, \"I was lost in my own mind,\" (BookA.pdf, Chapter 3)—while 'Book B' emphasizes "
            "external factors through vivid imagery, such as \"The empty streets echoed with silence,\" (BookB.epub, Page 15). "
            "This juxtaposition highlights differing narrative techniques in exploring the same theme."
        )
    },
    {
        "role": "user",
        "content": "Expand on how direct quotations strengthen the argument about social isolation in a novel."
    },
    {
        "role": "assistant",
        "content": (
            "Direct quotations serve as concrete evidence that anchors abstract concepts in tangible details. For instance, "
            "in 'Book A,' the quote \"Every day felt like a solitary battle\" (BookA.pdf, Page 35) transforms a general notion "
            "of isolation into a vivid, personal experience. This precise citation not only validates the argument but also "
            "provides the reader with a clear reference point to assess the emotional depth conveyed by the text."
        )
    },
    {
        "role": "user",
        "content": "Integrate evidence from multiple texts to compare the portrayals of social isolation across three books."
    },
    {
        "role": "assistant",
        "content": (
            "A comprehensive analysis reveals that each novel employs a distinct approach to depicting social isolation. "
            "In 'Book A,' isolation is internalized through reflective monologues (BookA.pdf, Chapter 4: \"I was alone even in a crowd\"). "
            "Conversely, 'Book B' portrays isolation as an external, environmental condition (BookB.epub, Page 12: \"The cold, empty streets spoke of alienation\"). "
            "Meanwhile, 'Book C' blends these perspectives by juxtaposing introspective dialogue with stark imagery (BookC.xml, Chapter 2: \"Silence filled the room, a void both seen and felt\"). "
            "This integrated evidence shows that social isolation is a multifaceted theme that varies according to narrative style and context."
        )
    },
    {
        "role": "user",
        "content": "Summarize how these different techniques collectively illustrate the complex nature of social isolation."
    },
    {
        "role": "assistant",
        "content": (
            "Collectively, the diverse techniques employed across these texts demonstrate that social isolation is not a single-faceted phenomenon. "
            "The introspective, internal focus in 'Book A,' the external, environmental depiction in 'Book B,' and the blended narrative of 'Book C' "
            "offer a layered understanding of isolation. By citing precise passages—such as (BookA.pdf, Page 35), (BookB.epub, Page 12), and "
            "(BookC.xml, Chapter 2)—the essays underscore that social isolation can be both a personal inner turmoil and a reflection of a broader societal condition. "
            "This multifaceted treatment provides a richer, more nuanced perspective on the theme."
        )
    }
]


def main():

    # environment set up for OpenAI and Pincecone APIs
    load_dotenv()
    
    openai_api_key = os.getenv("OPENAI_API_KEY")

    client = OpenAI(api_key=openai_api_key)
    pinecone_api_key = os.getenv("PINECONE_API_KEY")

    if not openai_api_key or not pinecone_api_key:
        raise ValueError("Need OPENAI_API_KEY and PINECONE_API_KEY in .env")

    # pinecone instance set up
    serverless = ServerlessSpec(cloud="aws", region="us-east-1")
    pc = Pinecone(api_key=pinecone_api_key, default_spec=serverless)

    index_name = "tower-demo-v0"
    index = pc.Index(index_name)

    # query to find matches to 'social isolation'
    theme = "social isolation"

    # embed theme
    emb = client.embeddings.create(model="text-embedding-ada-002", input=theme)
    query_vector = emb.data[0].embedding

    # query to db
    pine_res = index.query(
        vector=query_vector,
        top_k=9,
        namespace="ns1",
        include_metadata=True,
        include_values=False
    )

    # prepare context w/ direct references
    retrieved_passages = []
    for match in pine_res.get("matches", []):
        meta = match["metadata"]
        file_name = meta["file"]
        location_type = meta["location_type"]  # "page" or "chapter", depedending on book
        location_val = meta["location_val"]
        chunk_text = meta["text"]

        # quote size limit to maximize actual argument 
        short_quote = chunk_text[:200]
        if len(chunk_text) > 200:
            short_quote += "..."

        if location_type == "page":
            loc_str = f"Page {location_val}"
        elif location_type == "chapter":
            loc_str = f"Chapter {location_val}"
        else:
            loc_str = f"{location_type} {location_val}"  # fallback

        # e.g., (the_stranger.pdf, Page 2): "He sat alone in..."
        passage_str = f"({file_name}, {loc_str}): \"{short_quote}\""
        retrieved_passages.append(passage_str)

    # combine
    context_block = "\n\n".join(retrieved_passages)

    # message to be sent to model
    messages = []

    # added few-shot examples
    for example in FEW_SHOT_EXAMPLES:
        messages.append({"role": example["role"], "content": example["content"]})

    # user prompt
    user_prompt = f"""
    Below are excerpts from three novels referencing the theme of {theme}:

    {context_block}

    Write a full, 5-paragraph comparative book report analyzing how each novel addresses {theme} Reference the author.
    - Paragraph 1: Introduction & thesis (8-10 sentences)
    - Paragraphs 2-4: Compare/contrast the novels, referencing direct quotes (with page/chapter). (8-10 sentences)
    - Paragraph 5: Conclusion summarizing the argument. (8-10 sentences)

    Be sure to elaborate on quotes and combine them with in-depth analysis on how these quotes connect to the claim, and enhance the argument, 
    this essay MUST BE extremeley detailed, enough to where an expert would consider it "highq-quality" work

    Cite EACH and EVERY quote in this format: (author, X). Where X is the page number. If there is no page number associated and instead chapters, then cite as (author, chapter Y).
    Ensure the arguments are well-supported by direct evidence from these excerpts.
    """
    messages.append({"role": "user", "content": user_prompt})

    # chat completion
    response = client.chat.completions.create(model="gpt-4o-mini", # model agnostic, higher parameter + reasoning models will generally do better 
    # due to budget limitations, sticking to smaller model, but feel free to test with diferent OpenAI models
    messages=messages,
    temperature=0.7)
    final_essay = response.choices[0].message.content

    # save
    script_dir = os.path.dirname(__file__)  
    two_levels_up = os.path.abspath(os.path.join(script_dir, "..", ".."))

    report_path = os.path.join(two_levels_up, "final_book_report.txt")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_essay)

    print(f"\nSaved final book report to: {report_path}")


if __name__ == "__main__":
    main()