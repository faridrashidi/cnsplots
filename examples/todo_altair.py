import altair as alt
import seaborn as sns

import cnsplots as cns

cns.setup_altair()
iris = sns.load_dataset("iris")
tips = sns.load_dataset("tips")


p = (
    alt.Chart(iris)
    .mark_boxplot()
    .encode(
        x=alt.X("species", title="xlabel"),
        y=alt.Y("sepal_length", title="ylabel", scale=alt.Scale(zero=False)),
        color="species",
    )
    .properties(title="salam", height=120, width=80)
)
p
# print(p.to_json())
# alt.save(p, "plot.pdf")


p1 = (
    alt.Chart(iris)
    .mark_bar()
    .encode(
        x=alt.X("species", title="xlabel", sort=None),
        y=alt.Y("sepal_length", title="ylabel", scale=alt.Scale(zero=False)),
        color="species",
    )
)
p2 = p1.mark_text(dy=-8).encode(text="sepal_length")
(p1 + p2).properties(title="salam", height=120, width=80)


# alt.Chart(tips).mark_bar().encode(
#     y=alt.Y('day', stack="normalize"),
#     x='day',
#     color='sex'
# )


p = (
    alt.Chart(iris)
    .transform_density("sepal_length", as_=["sepal_length", "density"])
    .mark_area()
    .encode(x="sepal_length:Q", y="density:Q")
    .properties(height=120, width=120)
)
p


p = alt.Chart(iris).mark_point().encode(x="sepal_length", y="sepal_width")
p


iris["petal_width_range"] = iris["petal_width"] > 1
p = (
    alt.Chart(iris)
    .mark_rect()
    .encode(x="species", y="petal_width_range", color="petal_length")
)
p.properties(height=200, width=200)


alt.Chart(iris).mark_line().encode(x="petal_length", y="sepal_length")


# UpSet plot: https://github.com/hms-dbmi/upset-altair-notebook/blob/master/index.ipynb
