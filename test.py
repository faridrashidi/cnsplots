import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")
cns.figure(120, 100)
ax = cns.stackplot(data=tips, x="sex", y="day", width=0.4, normalize=True, addtip=True)
ax.set_title("Normalized Stacked Bar (with labels)")
cns.savefig("~/Desktop/salam.svg")
