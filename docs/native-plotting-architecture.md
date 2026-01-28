# Native Plotting Architecture

## Overview

This document outlines the proposed architectural changes to support native frontend plotting, replacing the current pre-rendered Plotly JSON approach.

## Current Architecture (Pre-rendered Plotly JSONs)

```
┌─────────────────────────────────────────────────────────────────────┐
│ GitHub Actions Workflow                                              │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│ │ Download    │ -> │ R Container │ -> │ Upload to   │              │
│ │ Simulations │    │ (simplot)   │    │ S3/DynamoDB │              │
│ └─────────────┘    └─────────────┘    └─────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ AWS Infrastructure                                                   │
│ ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│ │ S3 Bucket       │    │ DynamoDB        │    │ Lambda API      │  │
│ │ ~64K plot JSONs │    │ Plot index      │    │ Plot discovery  │  │
│ │ ~1.3 GB total   │    │ city+scenario+  │    │ Plot retrieval  │  │
│ └─────────────────┘    │ outcome+facet   │    └─────────────────┘  │
│                        └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Frontend (jheem-portal)                                              │
│ ┌─────────────────┐    ┌─────────────────┐                         │
│ │ Fetch plot JSON │ -> │ Render with     │                         │
│ │ (per facet)     │    │ react-plotly    │                         │
│ └─────────────────┘    └─────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
```

**Limitations:**
- 64K+ files to manage per full dataset
- ~1.3 GB storage
- Fixed faceting combinations (can only show pre-computed views)
- Each facet change requires new API call
- Styling locked to R/ggplot2 output

## Proposed Architecture (Summary Data + Native Plotting)

```
┌─────────────────────────────────────────────────────────────────────┐
│ GitHub Actions Workflow                                              │
│ ┌─────────────┐    ┌─────────────────────┐    ┌─────────────────┐  │
│ │ Download    │ -> │ R Container         │ -> │ Upload to S3    │  │
│ │ Simulations │    │ (extract_summary    │    │ (1 file/city)   │  │
│ │             │    │  _data.R)           │    │                 │  │
│ └─────────────┘    └─────────────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ AWS Infrastructure                                                   │
│ ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│ │ S3 Bucket       │    │ DynamoDB        │    │ Lambda API      │  │
│ │ 31 JSON files   │    │ (Optional)      │    │ GET /cities     │  │
│ │ ~47 MB gzipped  │    │ City metadata   │    │ GET /data/:city │  │
│ └─────────────────┘    └─────────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Frontend (jheem-portal)                                              │
│ ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│ │ Fetch city data │ -> │ Aggregate by    │ -> │ Render with     │  │
│ │ (once per city) │    │ user's facet    │    │ Recharts/Plotly │  │
│ │                 │    │ selection       │    │ (native)        │  │
│ └─────────────────┘    └─────────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- 31 files vs 64K files (~2000x fewer)
- ~47 MB vs ~1.3 GB storage (~28x smaller)
- Dynamic faceting (any combination supported)
- Single API call per city (cache locally)
- Full control over styling in frontend
- Modern, professional chart appearance

## Data Format

### Summary Data JSON Structure

```json
{
  "metadata": {
    "city": "C.12580",
    "city_label": "Baltimore-Columbia-Towson, MD",
    "scenarios": ["cessation", "brief_interruption", "prolonged_interruption"],
    "outcomes": {
      "incidence": {
        "id": "incidence",
        "display_name": "Incidence",
        "units": "infections",
        "display_as_percent": false,
        "corresponding_observed_outcome": "NULL"
      }
    },
    "dimensions": {
      "age": {"values": ["13-24 years", "25-34 years", ...], "label": "age"},
      "sex": {"values": ["heterosexual_male", "msm", "female"], "label": "sex"},
      "race": {"values": ["black", "hispanic", "other"], "label": "race"}
    }
  },
  "simulations": {
    "cessation": {
      "baseline": {
        "incidence": {
          "metadata": {...},
          "data": {
            "13-24 years_female_black": [
              {"year": 2010, "value": 29.62, "lower": 24.25, "upper": 37.28},
              {"year": 2011, "value": 26.45, "lower": 21.48, "upper": 33.05},
              ...
            ]
          }
        }
      },
      "intervention": {...}
    }
  },
  "observations": {
    "new": {
      "metadata": {
        "simset_outcome": "new",
        "data_manager_outcome": "diagnoses",
        "available_dimensions": ["year", "age", "sex"]
      },
      "data": {...}
    }
  }
}
```

### Size Estimates

| Cities | Uncompressed | Gzip Compressed |
|--------|--------------|-----------------|
| 1      | 15 MB        | 1.5 MB          |
| 31     | 465 MB       | 47 MB           |

## API Changes

### Current Endpoints (to deprecate)

```
GET /plots/cities         # List cities with available scenarios
GET /plots/search         # Search plots by city/scenario/outcome/facet
GET /plot                 # Get single plot JSON by S3 key
POST /plots/register      # Register new plot (GitHub Actions)
```

### New Endpoints

```
GET /v2/cities                    # List available cities
GET /v2/data/{city}               # Get complete summary data for city
GET /v2/data/{city}?compressed=1  # Get gzipped data (default)
```

### Example Response: GET /v2/cities

```json
{
  "cities": [
    {
      "code": "C.12580",
      "name": "Baltimore-Columbia-Towson, MD",
      "scenarios": ["cessation", "brief_interruption", "prolonged_interruption"],
      "data_url": "/v2/data/C.12580",
      "file_size_bytes": 1572864,
      "last_updated": "2025-12-11T00:00:00Z"
    }
  ],
  "total_cities": 31,
  "format_version": "2.0"
}
```

## Lambda Function Changes

### New Handler: get_city_data.py

```python
import boto3
import gzip
from io import BytesIO

s3 = boto3.client('s3')
BUCKET = 'jheem-summary-data'

def handler(event, context):
    city = event['pathParameters']['city']
    compressed = event.get('queryStringParameters', {}).get('compressed', '1') == '1'

    try:
        # Get from S3
        key = f'summary/{city}.json' + ('.gz' if compressed else '')
        response = s3.get_object(Bucket=BUCKET, Key=key)
        data = response['Body'].read()

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Content-Encoding': 'gzip' if compressed else 'identity',
                'Cache-Control': 'public, max-age=86400'  # 24 hour cache
            },
            'body': data,
            'isBase64Encoded': compressed
        }
    except s3.exceptions.NoSuchKey:
        return {'statusCode': 404, 'body': '{"error": "City not found"}'}
```

## GitHub Actions Workflow Changes

### Current: generate-plots.yml

- Downloads simulations
- Runs R container with `batch_plot_generator.R`
- Uploads individual plot JSONs to S3
- Registers each plot in DynamoDB

### New: generate-summary-data.yml

```yaml
name: Generate Summary Data

on:
  workflow_dispatch:
    inputs:
      cities:
        description: 'Cities to process (comma-separated or "all")'
        default: 'all'

jobs:
  generate:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        city: ${{ fromJson(needs.prepare.outputs.cities) }}
    steps:
      - name: Download simulations for city
        run: |
          aws s3 sync s3://jheem-data-production/simulations/ryan-white/base/${{ matrix.city }}* simulations/
          aws s3 sync s3://jheem-data-production/simulations/ryan-white/prerun/${{ matrix.city }}/ simulations/

      - name: Extract summary data
        run: |
          docker run --rm \
            -v $(pwd)/simulations:/app/simulations:ro \
            -v $(pwd)/output:/app/output \
            ${{ env.ECR_IMAGE }} \
            Rscript extract_summary_data.R \
              --city ${{ matrix.city }} \
              --output /app/output/${{ matrix.city }}.json

      - name: Compress and upload
        run: |
          gzip output/${{ matrix.city }}.json
          aws s3 cp output/${{ matrix.city }}.json.gz \
            s3://jheem-summary-data/summary/${{ matrix.city }}.json.gz \
            --content-encoding gzip
```

## Frontend Changes Required

### New Data Hook: useCityData.ts

```typescript
interface CityData {
  metadata: CityMetadata;
  simulations: Record<string, ScenarioData>;
  observations: Record<string, ObservationData>;
}

export function useCityData(cityCode: string) {
  const [data, setData] = useState<CityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/v2/data/${cityCode}`)
      .then(res => res.json())
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [cityCode]);

  return { data, loading, error };
}
```

### New Aggregation Utility: aggregateData.ts

```typescript
interface AggregationOptions {
  outcome: string;
  scenario: string;
  facetBy: ('age' | 'sex' | 'race')[];
}

export function aggregateSimulationData(
  data: CityData,
  options: AggregationOptions
): ChartData[] {
  const { outcome, scenario, facetBy } = options;
  const simData = data.simulations[scenario];

  // Get data at finest granularity
  const baselineData = simData.baseline[outcome].data;
  const interventionData = simData.intervention[outcome].data;

  // Aggregate across non-selected dimensions
  // ... aggregation logic

  return chartData;
}
```

### New Chart Component: SimulationChart.tsx

```typescript
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, Area } from 'recharts';

interface SimulationChartProps {
  data: ChartData[];
  showConfidenceInterval?: boolean;
  compareBaseline?: boolean;
}

export function SimulationChart({ data, showConfidenceInterval, compareBaseline }: SimulationChartProps) {
  return (
    <LineChart data={data}>
      <XAxis dataKey="year" />
      <YAxis />
      {showConfidenceInterval && (
        <Area dataKey="ci" fill="rgba(59, 130, 246, 0.2)" />
      )}
      <Line dataKey="value" stroke="#3b82f6" />
      {compareBaseline && (
        <Line dataKey="baseline" stroke="#9ca3af" strokeDasharray="5 5" />
      )}
      <Tooltip />
      <Legend />
    </LineChart>
  );
}
```

## Migration Plan

### Phase 1: Parallel Deployment (Week 1-2)
1. Add `extract_summary_data.R` to jheem-container-minimal
2. Create new S3 bucket for summary data
3. Add v2 API endpoints alongside existing v1
4. Generate summary data for all 31 cities

### Phase 2: Frontend Development (Week 2-3)
1. Create `useCityData` hook
2. Build aggregation utilities
3. Create new chart components with Recharts
4. Add feature flag to toggle between old/new

### Phase 3: Testing & Validation (Week 3-4)
1. Compare output with existing plots
2. Validate all faceting combinations work
3. Performance testing (load times, rendering)
4. User feedback on styling

### Phase 4: Cutover (Week 4)
1. Enable new frontend by default
2. Monitor for issues
3. Deprecate v1 API endpoints
4. Clean up old S3 data (64K files)

## Rollback Strategy

- Keep v1 endpoints available for 30 days after cutover
- Feature flag allows instant rollback to old frontend
- Old S3 data retained until validation complete
