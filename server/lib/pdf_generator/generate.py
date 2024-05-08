import base64
from datetime import datetime
import json
import pdfkit
from pathlib import Path
import openai
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

load_dotenv("../.env")

client = openai.Client(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


def load_image(image_path, image_type="jpeg"):
    image = Path("./lib/pdf_generator" + image_path).read_bytes()
    images_bytes = base64.b64encode(image).decode("utf-8")
    return f"data:image/{image_type};base64,{images_bytes}"


def scatter_plot_bytes(x, y, xLabel="", yLabel=""):
    plt.clf()
    plt.scatter(x, y, color="#6da7cd")
    plt.xlabel(xLabel)
    plt.ylabel(yLabel)

    plt.savefig("tmp.png")
    with open("tmp.png", "rb") as file:
        plot_bytes = base64.b64encode(file.read()).decode("utf-8")

    return plot_bytes


def bar_plot_bytes(x, y, xLabel="", yLabel=""):
    plt.clf()
    plt.bar(x, y, color="#6da7cd")
    plt.xlabel(xLabel)
    plt.ylabel(yLabel)

    plt.savefig("tmp.png")
    with open("tmp.png", "rb") as file:
        plot_bytes = base64.b64encode(file.read()).decode("utf-8")

    return plot_bytes


def generate_content(results, images=[]):

    prompt = f"""
    Metrics: {json.dumps(results["metrics"])}
    Context of the data: {results["context"]}
    
    Please return the following json object with filled in values:
    
    {{
      "title": "",
      "subttitle": "",
      "introduction": "",
      "coefficients": "",
      "metrics": "",
      "metric_image_descriptions": [],
      "section_titles": {{
        "main": "",
        "coefficients"; "",
        "metrics": "",
        "model_performance": ""
      }}
    }}
    
    title: A concise and informative string (4-8 words) representing the title of the report.
    subtitle: A brief string (6-18 words) representing the subtitle of the report.
    introduction: HTML-formatted text summarizing the report's purpose, findings, relevance to the business context, explanations for technical terms used within the report, interpretations of coefficients in the model, and explanations of metrics within context, including comparisons to examples or common values. It should encompass all information in approximately 3-4 paragraphs, presented in an easy-to-read and understand manner.
    coefficients: HTML-formatted list presenting model coefficients, their interpretations, and examples to aid understanding.
    metrics: HTML-formatted paragraph summarizing metrics, explaining their values within context, and comparing them to examples or common values.
    metric_image_descriptions: Short descriptions explaining the main characteristics of the provided images.
    section_titles:
      main: A concise and informative string (4-8 words) representing the title of the main section. Example: "OVERVIEW OF ATTRIBUTES AND THEIR IMPACT ON SALES"
      coefficients: A concise and informative string (4-8 words) representing the title of the coefficients section. Example: "Impact of Different Media on Sales"
      metrics: A concise and informative string (4-8 words) representing the title of the metrics section. Example: "Visual Insights"
      model_performance: A concise and informative string (4-8 words) representing the title of the model performance section. Example: "Model PerformanceIndicators"
    
    Guidelines:
    Use HTML tags for formatting in the introduction, coefficients, and metrics.
    Maintain concise and clear titles and subtitles.
    Provide a business-oriented introduction explaining the report's purpose and relevance.
    Include explanations for technical terms used within the report.
    Present coefficients in a list format with easy-to-understand interpretations and examples.
    Summarize metrics in a paragraph, explaining their values within context and comparing them to examples or common values.
    Keep the coefficients and metrics sections short, clear, and pertinent to the analysis. Use unordered lists for clarity.
    Limit numerical values to three decimal places.
    Highlight bullet-point titles in bold.
    Wrap numbers in <span class="number"></span> tags for styling.
    Utilize UTF-8 encoding for special characters.
    Present explanations from a non-technical, business perspective.
    Describe images briefly, focusing on key differences from other images.
    Following the JSON structure and guidelines strictly is crucial. Ensure no special characters or line breaks are added to the JSON object.
    
  """

    content = [{"type": "text", "text": prompt}]

    for image in images:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image}"},
            }
        )

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": content,
            },
        ],
    )

    return response.choices[0].message.content


def generate_pdf(filename, results):

    for data_key in results["data"]:
        results["data"][data_key] = [
            results["data"][data_key][key] for key in results["data"][data_key]
        ]

    used_metrics = results["metrics"]["Coefficients"].keys()
    reference_metric = results["metrics"]["Reference"]

    plots = [
        scatter_plot_bytes(
            results["data"][metric],
            results["data"][reference_metric],
            metric,
            reference_metric,
        )
        for metric in used_metrics
    ]

    coefficients_bar = bar_plot_bytes(
        results["metrics"]["Coefficients"].keys(),
        results["metrics"]["Coefficients"].values(),
        None,
        reference_metric,
    )

    # with open("tmp_content.json", "r") as file:
    raw_content = generate_content(
        results,
        [
            str(coefficients_bar),
        ]
        + [str(plot) for plot in plots],
    )
    content = json.loads(raw_content.replace("\n", ""))

    print(content)

    plots_html = ""

    for i in range(len(plots)):
        plot = plots[i]
        plots_html += f"""
        <td class="">
          <img src="data:image/png;base64,{plot}" width="100%" />
          <p class="small">{content["metric_image_descriptions"][i]}</p>
        </td>
      """

    date = datetime.now().strftime("%d.%m.%Y")

    body = f"""
      <html>
        <head>
        </head>
        <body>
          <header class="page-break large">
            <img class="first" src="{load_image('/images/bg-header.png', 'png')}" id="bg" />
            <img class="second" src="{load_image('/images/bg-header.png', 'png')}" id="bg" />
            <img src="{load_image('/images/bynd-logo-white.png', 'png')}" width="120" />
            <h1>{content["title"]}</h1>
            <h2>{content["subtitle"]}</h2>
            <p>{date}</p>
          </header>
          <div class="main">
            <section id="intro">
              <img id="outline" src="{load_image('/images/logo-outline.png', 'png')}" width="100%" />
              <h3>Introduction</h3>
              <p>{content["introduction"]}</p>
            </section>
            <section id="toc">
              <h3>Table of Contents</h3>
              <ul>
                <li><a href="#coefficients">{content["section_titles"]["coefficients"]}</a></li>
                <li><a href="#metrics">{content["section_titles"]["metrics"]}</a></li>
                <li><a href="#model_performance">{content["section_titles"]["model_performance"]}</a></li>
                <li><a href="#warning">AI Warning</a></li>
              </ul>
            </section>
          </div>
          <header class="page-break small">
            <img src="{load_image('/images/bg-header.png', 'png')}" id="bg" />
            <img src="{load_image('/images/bynd-logo-white.png', 'png')}" width="120" />
            <h1>{content["title"]}</h1>
            <h2>{content["subtitle"]}</h2>
          </header>
          <div class="main">
            <h3>{content["section_titles"]["main"]}</h3>
            <h4 id="coefficients">{content["section_titles"]["coefficients"]}</h4>
            <table width="100%" border="0" cellpadding="0px" cellspacing="16px">
              <tr class="center-vertically">
                <td class="center-vertically">
                  <img src="data:image/png;base64,{coefficients_bar}" width="100%"/>
                </td>
                <td class="center-vertically">
                    {content["coefficients"]}
                </td>
              </tr>
            </table>
            <h4 id="metrics">{content["section_titles"]["metrics"]}</h4>
            <table width="100%" border="0" cellpadding="0px" cellspacing="16px">
              <tr>
                {plots_html}
              </tr>
            </table>
            
            <h4 id="model_performance">{content["section_titles"]["model_performance"]}</h4>
            {content["metrics"]}
            
            <section id="warning">
              <h3>AI Warning</h3>
              <p>This document contains content that has been generated by an artificial intelligence model. While the information presented is based on data-driven analysis, it is important to exercise caution and critical thinking when interpreting the results. Human oversight and expert judgment are essential to ensure the accuracy and relevance of the insights provided.</p>
            </section>
          </div>
        </body>
        </html>
      """

    options = {
        "page-size": "A4",
        "margin-top": "0.0in",
        "margin-right": "0.0in",
        "margin-bottom": "0.4in",
        "margin-left": "0.0in",
    }

    pdfkit.from_string(
        body,
        f"{filename}.pdf",
        css="./lib/pdf_generator/style.css",
        options=options,
    )
