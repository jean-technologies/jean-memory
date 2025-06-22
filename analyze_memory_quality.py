#!/usr/bin/env python3
"""
Memory Processing Quality Analysis and Optimization Tool
Analyzes the quality of batch-processed memories and provides optimization recommendations.
"""

import json
import argparse
from datetime import datetime
from collections import Counter, defaultdict
import re

def load_data(file_path):
    """Load processed memory data"""
    with open(file_path, 'r') as f:
        return json.load(f)

def analyze_confidence_distribution(memories):
    """Analyze confidence level distribution"""
    confidence_counts = Counter(m.get('confidence', 'unknown') for m in memories)
    total = len(memories)
    
    print("📊 CONFIDENCE DISTRIBUTION")
    print("-" * 40)
    for conf, count in confidence_counts.most_common():
        percentage = (count / total) * 100
        print(f"   {conf.upper()}: {count}/{total} ({percentage:.1f}%)")
    print()
    
    return confidence_counts

def analyze_temporal_extraction(memories):
    """Analyze temporal keyword extraction quality"""
    with_keywords = sum(1 for m in memories if m.get('temporal_keywords'))
    total = len(memories)
    
    # Collect all temporal keywords
    all_keywords = []
    for m in memories:
        all_keywords.extend(m.get('temporal_keywords', []))
    
    keyword_freq = Counter(all_keywords)
    
    print("🕒 TEMPORAL EXTRACTION ANALYSIS")
    print("-" * 40)
    print(f"   Memories with temporal keywords: {with_keywords}/{total} ({with_keywords/total*100:.1f}%)")
    print(f"   Total unique keywords: {len(keyword_freq)}")
    
    if keyword_freq:
        print(f"   Most common keywords:")
        for keyword, count in keyword_freq.most_common(10):
            print(f"      '{keyword}': {count}")
    print()
    
    return with_keywords, keyword_freq

def analyze_reasoning_patterns(memories):
    """Analyze reasoning patterns to identify optimization opportunities"""
    reasoning_patterns = defaultdict(list)
    
    for i, memory in enumerate(memories):
        reasoning = memory.get('reasoning', '').lower()
        confidence = memory.get('confidence', 'unknown')
        
        # Categorize reasoning patterns
        if 'creation date' in reasoning or 'no specific' in reasoning:
            reasoning_patterns['fallback_to_creation'].append((i, confidence, memory))
        elif 'explicit' in reasoning or 'states' in reasoning:
            reasoning_patterns['explicit_date'].append((i, confidence, memory))
        elif 'temporal' in reasoning or 'keyword' in reasoning:
            reasoning_patterns['temporal_inference'].append((i, confidence, memory))
        elif 'likely' in reasoning or 'around' in reasoning:
            reasoning_patterns['contextual_inference'].append((i, confidence, memory))
        else:
            reasoning_patterns['other'].append((i, confidence, memory))
    
    print("🧠 REASONING PATTERN ANALYSIS")
    print("-" * 40)
    for pattern, items in reasoning_patterns.items():
        print(f"   {pattern.replace('_', ' ').title()}: {len(items)}")
        
        # Show confidence distribution for this pattern
        conf_dist = Counter(item[1] for item in items)
        print(f"      Confidence: {dict(conf_dist)}")
    print()
    
    return reasoning_patterns

def identify_optimization_opportunities(memories):
    """Identify specific optimization opportunities"""
    opportunities = {
        'low_confidence_with_potential': [],
        'missing_temporal_keywords': [],
        'vague_temporal_context': [],
        'could_be_more_specific': []
    }
    
    for i, memory in enumerate(memories):
        content = memory.get('original_content', '')
        confidence = memory.get('confidence', 'unknown')
        keywords = memory.get('temporal_keywords', [])
        temporal_context = memory.get('temporal_context', '')
        reasoning = memory.get('reasoning', '')
        
        # Low confidence but content has temporal indicators
        if confidence == 'low':
            temporal_indicators = re.findall(r'\b(yesterday|today|tomorrow|last|this|next|morning|afternoon|evening|night|monday|tuesday|wednesday|thursday|friday|saturday|sunday|january|february|march|april|may|june|july|august|september|october|november|december|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{1,2}-\d{1,2})\b', content.lower())
            
            if temporal_indicators:
                opportunities['low_confidence_with_potential'].append({
                    'index': i,
                    'content': content[:60] + '...',
                    'found_indicators': temporal_indicators,
                    'current_reasoning': reasoning
                })
        
        # Missing temporal keywords despite having temporal words
        if not keywords:
            temporal_words = re.findall(r'\b(yesterday|today|tomorrow|last|this|next|first|started|finished|completed|began|ended)\b', content.lower())
            if temporal_words:
                opportunities['missing_temporal_keywords'].append({
                    'index': i,
                    'content': content[:60] + '...',
                    'potential_keywords': temporal_words
                })
        
        # Vague temporal context
        if 'likely around' in temporal_context.lower() or 'approximately' in temporal_context.lower():
            opportunities['vague_temporal_context'].append({
                'index': i,
                'content': content[:60] + '...',
                'vague_context': temporal_context
            })
        
        # Could be more specific
        if confidence == 'medium' and len(keywords) <= 1:
            opportunities['could_be_more_specific'].append({
                'index': i,
                'content': content[:60] + '...',
                'current_keywords': keywords,
                'confidence': confidence
            })
    
    print("🔧 OPTIMIZATION OPPORTUNITIES")
    print("-" * 40)
    
    for category, items in opportunities.items():
        if items:
            print(f"   {category.replace('_', ' ').title()}: {len(items)} memories")
            for item in items[:3]:  # Show top 3 examples
                print(f"      • {item['content']}")
            if len(items) > 3:
                print(f"      ... and {len(items) - 3} more")
            print()
    
    return opportunities

def analyze_batch_efficiency(data):
    """Analyze batch processing efficiency"""
    print("⚡ BATCH PROCESSING EFFICIENCY")
    print("-" * 40)
    
    total_memories = data.get('total_memories', 0)
    api_calls = data.get('total_api_calls', 0)
    cost_reduction = data.get('cost_reduction_percentage', 0)
    
    print(f"   Total memories processed: {total_memories}")
    print(f"   API calls used: {api_calls}")
    print(f"   Individual calls would have been: {total_memories}")
    print(f"   Cost reduction: {cost_reduction:.1f}%")
    print(f"   Efficiency ratio: {total_memories/api_calls:.1f} memories per API call")
    print()

def generate_optimization_recommendations(confidence_dist, opportunities, keyword_freq):
    """Generate specific optimization recommendations"""
    print("💡 OPTIMIZATION RECOMMENDATIONS")
    print("-" * 40)
    
    total_memories = sum(confidence_dist.values())
    low_conf_ratio = confidence_dist.get('low', 0) / total_memories
    
    recommendations = []
    
    # Confidence-based recommendations
    if low_conf_ratio > 0.3:
        recommendations.append(
            "🔴 HIGH PRIORITY: >30% low confidence - Consider improving temporal extraction prompts"
        )
    elif low_conf_ratio > 0.2:
        recommendations.append(
            "🟡 MEDIUM PRIORITY: >20% low confidence - Review and refine processing logic"
        )
    
    # Temporal keyword recommendations
    if len(opportunities['missing_temporal_keywords']) > 5:
        recommendations.append(
            "🔍 KEYWORD EXTRACTION: Many memories missing temporal keywords - enhance keyword detection"
        )
    
    # Batch size recommendations
    if len(opportunities['low_confidence_with_potential']) > 3:
        recommendations.append(
            "📦 BATCH SIZE: Consider smaller batches for better temporal analysis quality"
        )
    
    # Prompt engineering recommendations
    if len(opportunities['vague_temporal_context']) > 5:
        recommendations.append(
            "📝 PROMPT ENGINEERING: Many vague temporal contexts - improve specificity in prompts"
        )
    
    # Model recommendations
    if confidence_dist.get('high', 0) / total_memories < 0.1:
        recommendations.append(
            "🤖 MODEL TUNING: <10% high confidence - consider fine-tuning or different model approach"
        )
    
    if not recommendations:
        recommendations.append("✅ EXCELLENT: Processing quality is very good, no major optimizations needed")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    print()

def export_optimization_data(opportunities, output_file):
    """Export detailed optimization data for further analysis"""
    optimization_data = {
        'timestamp': datetime.now().isoformat(),
        'optimization_opportunities': opportunities,
        'summary': {
            'total_opportunities': sum(len(items) for items in opportunities.values()),
            'categories': list(opportunities.keys())
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(optimization_data, f, indent=2)
    
    print(f"📄 Detailed optimization data exported to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Analyze memory processing quality')
    parser.add_argument('--input', required=True, help='Preprocessed memories JSON file')
    parser.add_argument('--export-optimizations', help='Export optimization opportunities to JSON file')
    
    args = parser.parse_args()
    
    print("🔍 MEMORY PROCESSING QUALITY ANALYSIS")
    print("=" * 60)
    
    # Load data
    try:
        data = load_data(args.input)
        memories = data.get('memories', [])
        
        if not memories:
            print("❌ No memories found in the input file")
            return
        
        print(f"📊 Analyzing {len(memories)} processed memories...")
        print()
        
        # Run analyses
        confidence_dist = analyze_confidence_distribution(memories)
        with_keywords, keyword_freq = analyze_temporal_extraction(memories)
        reasoning_patterns = analyze_reasoning_patterns(memories)
        opportunities = identify_optimization_opportunities(memories)
        analyze_batch_efficiency(data)
        generate_optimization_recommendations(confidence_dist, opportunities, keyword_freq)
        
        # Export optimization data if requested
        if args.export_optimizations:
            export_optimization_data(opportunities, args.export_optimizations)
        
        print("✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 