import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Load data
with open('memory_behavior.json', 'r') as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(data)

# Parse timestamps and numeric fields
df['user_created_at'] = pd.to_datetime(df['user_created_at'])
df['first_memory_at'] = pd.to_datetime(df['first_memory_at'])
df['last_memory_at'] = pd.to_datetime(df['last_memory_at'])
df['active_days_span'] = df['active_days_span'].astype(float)
df['memory_count'] = df['memory_count'].astype(int)
df['avg_hours_between_memories'] = pd.to_numeric(df['avg_hours_between_memories'], errors='coerce')
df['days_since_last_memory'] = df['days_since_last_memory'].astype(float)
df['memories_per_active_day'] = pd.to_numeric(df['memories_per_active_day'], errors='coerce')
df['memories_per_signup_day'] = pd.to_numeric(df['memories_per_signup_day'], errors='coerce')
df['memories_today'] = df['memories_today'].astype(int)

# Advanced Metric Engineering
def calc_burstiness(row):
    # Coefficient of Variation of memory ingestion intervals
    times = pd.to_datetime(row['memory_timestamps'])
    if len(times) <= 2:
        return 0
    diffs = (times[1:] - times[:-1]).total_seconds() / 3600
    return np.std(diffs) / np.mean(diffs) if np.mean(diffs) != 0 else 0

def calc_early_activity_ratio(row, hours=24):
    times = pd.to_datetime(row['memory_timestamps'])
    if len(times) == 0:
        return np.nan
    first = times[0]
    early_count = sum((t - first).total_seconds() / 3600 < hours for t in times)
    return early_count / len(times)

def calc_longest_streak(row):
    times = pd.to_datetime(row['memory_timestamps'])
    if len(times) == 0:
        return 0
    days = sorted(set(t.date() for t in times))
    streak, max_streak, prev = 1, 1, days[0]
    for d in days[1:]:
        if (d - prev).days == 1:
            streak += 1
        else:
            streak = 1
        max_streak = max(max_streak, streak)
        prev = d
    return max_streak

def calc_inactivity_windows(row):
    times = pd.to_datetime(row['memory_timestamps'])
    if len(times) <= 1:
        return 0
    diffs = [(t2 - t1).days for t1, t2 in zip(times[:-1], times[1:])]
    return max(diffs)

df['burstiness'] = df.apply(calc_burstiness, axis=1)
df['early_activity_ratio'] = df.apply(calc_early_activity_ratio, axis=1)
df['longest_streak_days'] = df.apply(calc_longest_streak, axis=1)
df['max_inactivity_gap_days'] = df.apply(calc_inactivity_windows, axis=1)

# Churn/engagement risk: High values = more at risk
df['churn_risk_score'] = (
    0.4 * (df['days_since_last_memory'] / (df['active_days_span']+1)) +
    0.3 * (1 - df['early_activity_ratio'].fillna(0)) +
    0.2 * (df['max_inactivity_gap_days'] / (df['active_days_span']+1)) +
    0.1 * (1 - (df['longest_streak_days'] / (df['active_days_span']+1)))
)
df['churn_risk_score'] = df['churn_risk_score'].fillna(0).clip(0, 1)

# Feature scaling for clustering
engagement_features = [
    'memory_count',
    'memories_per_active_day',
    'memories_per_signup_day',
    'burstiness',
    'early_activity_ratio',
    'longest_streak_days',
    'max_inactivity_gap_days',
    'avg_hours_between_memories',
    'days_since_last_memory'
]
df_cluster = df[engagement_features].fillna(0)
scaler = StandardScaler()
df_scaled = scaler.fit_transform(df_cluster)

# KMeans clustering for user personas
kmeans = KMeans(n_clusters=4, random_state=42)
df['engagement_cluster'] = kmeans.fit_predict(df_scaled)

# Visualize clusters
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='memories_per_signup_day', y='burstiness', hue='engagement_cluster', palette='Set2')
plt.title('User Engagement Personas: Memories per Signup Day vs. Burstiness')
plt.xlabel('Memories per Signup Day')
plt.ylabel('Burstiness (CV of time between memories)')
plt.legend(title='Cluster')
plt.show()

# Trends & Gradients
plt.figure(figsize=(10, 6))
sns.histplot(df['churn_risk_score'], bins=20, kde=True)
plt.title('Distribution of Churn Risk Score')
plt.xlabel('Churn Risk Score')
plt.show()

# Show persona statistics
persona_stats = df.groupby('engagement_cluster')[engagement_features + ['churn_risk_score']].mean()
print("\n=== User Engagement Personas (Cluster Means) ===\n")
print(persona_stats.round(2))

# Actionable Insights
print("\n=== Suggested Actions by Persona Cluster ===\n")
for cluster, stats in persona_stats.iterrows():
    print(f"Persona {cluster}:")
    if stats['churn_risk_score'] > 0.7:
        print("  - At high churn risk. Suggest push notifications, onboarding emails, or gamification to re-engage.")
    elif stats['memories_per_signup_day'] > 1 and stats['burstiness'] < 0.5:
        print("  - Power user! Consider offering advanced features, badges, or early access programs.")
    elif stats['memories_per_signup_day'] < 0.2:
        print("  - Low engagement. Survey these users or streamline entry points to boost initial experience.")
    else:
        print("  - Moderate engagement. Personalized tips and celebrating streaks may boost retention.")
    print()

# For full report, save to CSV:
df.to_csv('user_engagement_analysis.csv', index=False)
