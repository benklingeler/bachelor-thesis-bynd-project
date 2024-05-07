import base64
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
      "metric_image_descriptions": []
    }}
    
    - title: A string that represents the title of the report.
    - subtitle: A string that represents the subtitle of the report.
    - introduction: A string that represents the introduction of the report. It should explain the report and its purpose from a business perspective. It should also summarize the key insights and findings from the analysis.
    - coefficients: String containing a list of the coefficients of the model and an explanation of their meaning and relevance to the analysis.
    - metrics: String containing a list of the used metrics and an explanation of their meaning and relevance to the analysis.
    
    Follow the guidelines below to fill in the values:
    - Use html tags to format the text within the strings for introduction and metrics.
    - Ensure that the title and subtitle are concise and informative.
    - Provide a clear and concise introduction that explains the purpose of the report and its relevance to the business context.
    - Keep the metrics and coefficients section short, clear, and relevant to the analysis. Dont add an heading. Only the metrics or coefficients itself in form of an list.
    - Shorten numbers to 3 decimal places.
    - Use unordered lists for the metrics and coefficients.
    - Highlight bullet-point titles by making them bold.
    - Wrap numbers in <span class="number"></span> tags to style them as code.
    - Use UTF-8 encoding for special characters.
    - Explain everything from a business perspective and avoid technical terms. The audience is non-technical.
    - Use the images provided and explain them in metric_image_descriptions. Keep the explaination short and only focus on the main characteristic. Highlight how the data in the image differs from the other images.
    
    Very important: Following the structure of the json for the answer and the guidelines is very important. Please follow them strictly.
    Make sure to not add any special characters or line breaks to the json object.
    
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

    plots_html = f""""""

    for i in range(len(plots)):
        plot = plots[i]
        plots_html += f"""
        <td class="">
          <img src="data:image/png;base64,{plot}" width="100%" />
          <p class="small">{content["metric_image_descriptions"][i]}</p>
        </td>
      """

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
            <p>06.05.2024</p>
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
                <li><a href="#coefficients">Impact of Different Media on Sales</a></li>
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
            <h3>Overview of Attributes and Their Impact on Sales</h3>
            <h4 id="coefficients">Impact of Different Media on Sales</h4>
            <table width="100%" border="0" cellpadding="0px" cellspacing="16px">
              <tr>
                <td>
                  <img src="data:image/png;base64,{coefficients_bar}" width="100%"/>
                </td>
                <td class="">
                  <div class="center-vertically">
                    {content["coefficients"].replace("ul>", "div>").replace("li>", "p>").replace("-", "")}
                  </div>
                </td>
              </tr>
            </table>
            <h4>Visual Insights</h4>
            <table width="100%" border="0" cellpadding="0px" cellspacing="16px">
              <tr>
                {plots_html}
              </tr>
            </table>
            
            <h4>Model Performance Indicators</h4>
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
