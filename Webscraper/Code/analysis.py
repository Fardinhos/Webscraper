import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re
from scipy.stats import pearsonr

# load and clean the data
df_scifi = pd.read_csv('top_scifi.csv')
df_action = pd.read_csv('top_action.csv')
df_horror = pd.read_csv('top_horror.csv')

df_scifi['Genre'], df_action['Genre'], df_horror['Genre'] = 'Sci-Fi', 'Action', 'Horror'
df = pd.concat([df_scifi, df_action, df_horror], ignore_index=True).drop_duplicates(subset=['Title'])

def duration_to_min(val):
    if pd.isna(val): return np.nan
    h, m = re.search(r'(\d+)h', str(val)), re.search(r'(\d+)m', str(val))
    return (int(h.group(1))*60 if h else 0) + (int(m.group(1)) if m else 0)

df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
df['Rating_100'] = df['Rating'] * 10 
df['Metascore'] = pd.to_numeric(df['Metascore'], errors='coerce')
df['Duration_mins'] = df['Duration'].apply(duration_to_min)
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')

df_clean = df.dropna(subset=['Rating', 'Rating_100', 'Metascore', 'Duration_mins', 'Year']).copy()

# remove the outliers so the graph looks better
year_1st_percentile = df_clean['Year'].quantile(0.01)
df_clean = df_clean[(df_clean['Year'] >= year_1st_percentile)]


# create the three visualizations
sns.set_theme(style="whitegrid", context="talk", palette="deep")
fig, axes = plt.subplots(1, 3, figsize=(24, 8))
fig.suptitle('IMDb Top Movies', fontsize=22, fontweight='bold', y=0.98)

# plot 1: compare critic scores vs audience ratings
sns.scatterplot(data=df_clean, x='Metascore', y='Rating_100', hue='Genre', alpha=0.7, s=100, ax=axes[0])

min_val = min(df_clean['Metascore'].min(), df_clean['Rating_100'].min())
axes[0].plot([min_val, 100], [min_val, 100], color='black', linestyle='--', linewidth=2, label='Parity Line (1:1 Agreement)')

r_overall, _ = pearsonr(df_clean['Metascore'], df_clean['Rating_100'])
stats_text_q1 = f"Correlation (r):\nOverall: {r_overall:.2f}\n"

for genre in ['Sci-Fi', 'Action', 'Horror']:
    genre_data = df_clean[df_clean['Genre'] == genre]
    if len(genre_data) > 2:
        r_genre, _ = pearsonr(genre_data['Metascore'], genre_data['Rating_100'])
        stats_text_q1 += f"{genre}: {r_genre:.2f}\n"

axes[0].text(0.05, 0.95, stats_text_q1.strip(), transform=axes[0].transAxes, fontsize=12, 
             verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray'))

axes[0].set_title('Q1: Do Audiences and Critics Agree?\n(Dots above the line indicate audience preference)', fontsize=14, pad=15)
axes[0].set_xlabel('Professional Critic Score (Metascore)', fontweight='bold')
axes[0].set_ylabel('Audience Score (IMDb Rating x 10)', fontweight='bold')
axes[0].legend(fontsize='small', loc='lower right')

# plot 2: find the best movie length
sns.kdeplot(data=df_clean, x='Duration_mins', y='Rating', fill=True, cmap="mako", thresh=0.05, alpha=0.9, ax=axes[1])

axes[1].set_title('Q2: The Runtime "Sweet Spot"\n(Density heatmap showing where top-rated movies cluster)', fontsize=14, pad=15)
axes[1].set_xlabel('Movie Duration (Minutes)', fontweight='bold')
axes[1].set_ylabel('Audience Score (IMDb Rating)', fontweight='bold')

# plot 3: do newer movies get better ratings
sns.scatterplot(data=df_clean, x='Year', y='Rating', hue='Genre', alpha=0.4, s=60, legend=False, ax=axes[2])

colors = sns.color_palette("deep") 
stats_text_q3 = "Correlations (r):\n"

for idx, genre in enumerate(df_clean['Genre'].unique()):
    genre_data = df_clean[df_clean['Genre'] == genre]
    
    # calculate pearson correlation for year vs rating
    if len(genre_data) > 2:
        r_year, _ = pearsonr(genre_data['Year'], genre_data['Rating'])
        stats_text_q3 += f"{genre}: {r_year:.2f}\n"
    
    sns.regplot(data=genre_data, x='Year', y='Rating', scatter=False, ax=axes[2], 
                color=colors[idx], label=f"{genre} Trend", line_kws={'linewidth': 3})

axes[2].text(0.05, 0.05, stats_text_q3.strip(), transform=axes[2].transAxes, fontsize=12, 
             verticalalignment='bottom', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray'))

axes[2].set_title('Q3: Evolution of Genre Acclaim (1970-Present)\n(Historical regression trends over decades)', fontsize=14, pad=15)
axes[2].set_xlabel('Release Year', fontweight='bold')
axes[2].set_ylabel('Audience Score (IMDb Rating)', fontweight='bold')
axes[2].legend(fontsize='small', loc='lower right')

# save the graph
plt.tight_layout()
plt.subplots_adjust(top=0.85) 
fig.savefig('graphs.png', dpi=300, bbox_inches='tight')
print("Successfully generated graphs.png")