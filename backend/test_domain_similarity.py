from app.services.vector_service import embeddings
from app.services.domain_similarity_service import get_best_matching_domain

text = "The US Bureau of Labor Statistics reported headline CPI rose 3.6% year-on-year in April, exceeding the 3.2% consensus estimate. Core inflation, which excludes food and energy, held at 3.9% driven by persistent services costs. GDP growth for Q1 came in at 1.8% annualised, below the 2.4% forecast, raising stagflation concerns. Unemployment ticked up to 4.2%, its highest reading in eighteen months, as hiring in the manufacturing and construction sectors slowed. Analysts revised their full-year growth outlook downward while simultaneously lifting inflation forecasts — a combination that historically has been supportive for gold as a hedge against both currency debasement and economic uncertainty."

document_embedding = embeddings.embed_query(text)

result = get_best_matching_domain(document_embedding)

print(result)