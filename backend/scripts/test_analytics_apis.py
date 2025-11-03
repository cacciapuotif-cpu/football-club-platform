"""Test script for Advanced Analytics APIs."""

import asyncio
import httpx
from typing import Optional


class AnalyticsAPITester:
    """Test suite for analytics endpoints."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_prefix = f"{base_url}/api/v1/advanced-analytics"

    async def test_health(self) -> bool:
        """Test if backend is running."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/healthz", timeout=5.0)
                if response.status_code == 200:
                    print("✅ Backend is running")
                    return True
                else:
                    print(f"❌ Backend health check failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Cannot connect to backend: {e}")
            print(f"   Make sure backend is running on {self.base_url}")
            return False

    async def get_sample_player_id(self) -> Optional[str]:
        """Get a sample player ID from the database."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/players",
                    timeout=10.0,
                    params={"limit": 1}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        player_id = data[0].get("id")
                        print(f"   Using player ID: {player_id}")
                        return player_id
        except Exception as e:
            print(f"   Warning: Could not fetch player ID: {e}")
        return None

    async def get_sample_team_id(self) -> Optional[str]:
        """Get a sample team ID from the database."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/teams",
                    timeout=10.0,
                    params={"limit": 1}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        team_id = data[0].get("id")
                        print(f"   Using team ID: {team_id}")
                        return team_id
        except Exception as e:
            print(f"   Warning: Could not fetch team ID: {e}")
        return None

    async def test_player_analysis(self, player_id: str):
        """Test player analysis endpoint."""
        print("\n📊 TEST 1: Player Analysis API")
        print(f"   GET {self.api_prefix}/players/{player_id}/analysis")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_prefix}/players/{player_id}/analysis",
                    params={"matches": 10},
                    timeout=15.0
                )

                if response.status_code == 200:
                    data = response.json()
                    print("   ✅ SUCCESS")
                    print(f"   Player: {data['player']['name']}")
                    print(f"   Position: {data['player']['position']}")
                    print(f"   Overall Rating: {data['player']['overall_rating']:.2f}")
                    print(f"   Performance Index: {data['analytics']['aggregate_stats']['performance_index']:.2f}")
                    print(f"   Form Prediction: {data['analytics']['form_prediction']:.2f}")
                    print(f"   Performance Trend: {data['analytics']['performance_trend']}")
                    print(f"   Strengths: {', '.join(data['analytics']['strengths'])}")
                    return True
                else:
                    print(f"   ❌ FAILED - Status: {response.status_code}")
                    print(f"   Error: {response.text}")
                    return False

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            return False

    async def test_scouting_recommendations(self, team_id: str):
        """Test scouting recommendations endpoint."""
        print("\n🔍 TEST 2: Scouting Recommendations API")
        print(f"   GET {self.api_prefix}/scouting/teams/{team_id}/recommendations")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_prefix}/scouting/teams/{team_id}/recommendations",
                    params={
                        "position": "FW",
                        "max_age": 28,
                        "max_budget": 50000000,
                        "min_rating": 6.0
                    },
                    timeout=20.0
                )

                if response.status_code == 200:
                    data = response.json()
                    print("   ✅ SUCCESS")
                    print(f"   Total Recommendations: {data['summary']['total_players']}")
                    print(f"   Strong Buys: {data['summary']['strong_buys']}")
                    print(f"   Buys: {data['summary']['buys']}")
                    print(f"   Considers: {data['summary']['considers']}")

                    if data['recommendations']:
                        print("\n   Top 3 Recommendations:")
                        for i, rec in enumerate(data['recommendations'][:3], 1):
                            player = rec['player']
                            analytics = rec['analytics']
                            print(f"\n   {i}. {player['name']} ({player['position']}, {player['age']}y)")
                            print(f"      Rating: {player['overall_rating']:.2f} | Form: {analytics['form_prediction']:.2f}")
                            print(f"      Value Score: {analytics['value_score']:.2f}")
                            print(f"      Recommendation: {rec['recommendation']} (Confidence: {rec['confidence']}%)")
                    return True
                else:
                    print(f"   ❌ FAILED - Status: {response.status_code}")
                    print(f"   Error: {response.text}")
                    return False

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            return False

    async def test_team_analysis(self, team_id: str):
        """Test team analysis endpoint."""
        print("\n🏆 TEST 3: Team Analysis API")
        print(f"   GET {self.api_prefix}/teams/{team_id}/analysis")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_prefix}/teams/{team_id}/analysis",
                    timeout=15.0
                )

                if response.status_code == 200:
                    data = response.json()
                    print("   ✅ SUCCESS")
                    print(f"   Total Players: {data['total_players']}")
                    print(f"   Average Rating: {data['average_rating']:.2f}")
                    print(f"   Position Distribution: {data['position_distribution']}")
                    print(f"   Performance by Position: {data['performance_by_position']}")
                    print(f"   Top Performers: {len(data['top_performers'])}")
                    print(f"   Areas for Improvement: {', '.join(data['areas_for_improvement'])}")
                    return True
                else:
                    print(f"   ❌ FAILED - Status: {response.status_code}")
                    print(f"   Error: {response.text}")
                    return False

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            return False

    async def test_performance_trend(self, player_id: str):
        """Test performance trend endpoint."""
        print("\n📈 TEST 4: Performance Trend API")
        print(f"   GET {self.api_prefix}/players/{player_id}/trend")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_prefix}/players/{player_id}/trend",
                    params={"period_days": 60},
                    timeout=15.0
                )

                if response.status_code == 200:
                    data = response.json()
                    print("   ✅ SUCCESS")
                    print(f"   Period: {data['period']}")
                    print(f"   Data Points: {len(data['trend_data'])}")
                    print(f"   Average Performance: {data['summary']['average_performance']:.2f}")
                    print(f"   Trend: {data['summary']['trend']}")
                    print(f"   Consistency: {data['summary']['consistency']:.1f}%")
                    return True
                else:
                    print(f"   ❌ FAILED - Status: {response.status_code}")
                    print(f"   Error: {response.text}")
                    return False

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            return False

    async def run_all_tests(self):
        """Run all API tests."""
        print("="*70)
        print("🧪 ADVANCED ANALYTICS API TEST SUITE")
        print("="*70)

        # Check if backend is running
        if not await self.test_health():
            print("\n❌ Backend is not running. Please start it first:")
            print("   cd backend")
            print("   uvicorn app.main:app --reload")
            return False

        # Get sample IDs
        print("\n📋 Fetching sample data...")
        player_id = await self.get_sample_player_id()
        team_id = await self.get_sample_team_id()

        if not player_id or not team_id:
            print("\n❌ No data found. Please run the seed script first:")
            print("   cd backend")
            print("   python scripts/complete_seed_advanced.py")
            return False

        # Run tests
        results = []
        results.append(await self.test_player_analysis(player_id))
        results.append(await self.test_scouting_recommendations(team_id))
        results.append(await self.test_team_analysis(team_id))
        results.append(await self.test_performance_trend(player_id))

        # Summary
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)

        passed = sum(results)
        total = len(results)

        print(f"   Passed: {passed}/{total}")
        print(f"   Failed: {total - passed}/{total}")

        if passed == total:
            print("\n   ✅ ALL TESTS PASSED! 🎉")
            print("\n   🚀 Your Advanced Analytics system is fully functional!")
            print("\n   📖 Next steps:")
            print("      • Check API documentation: http://localhost:8000/docs")
            print("      • Read ADVANCED_ANALYTICS_GUIDE.md for detailed examples")
            print("      • Integrate with your frontend application")
            return True
        else:
            print(f"\n   ⚠️  {total - passed} test(s) failed")
            print("   Please check the errors above and fix the issues")
            return False


async def main():
    """Main test function."""
    tester = AnalyticsAPITester()
    success = await tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
