"use client"

import { useState, useMemo } from "react"

// Mock data matching your structure
const mockCommunities = [
  {
    Name: "Wattworks Amsterdam",
    Sport: "Cycling classes, personal coaching",
    email: "info@wattworks.nl",
    website: "https://www.wattworks.nl/",
    Location: "Van Hallstraat 9D 1051GW Amsterdam",
    Cost: "Paid",
    "Student-based": "No",
    image_url: "",
  },
  {
    Name: "Amsterdam Running Club",
    Sport: "Running, Trail running",
    email: "info@amsterdamrunning.com",
    website: "https://amsterdamrunning.com",
    Location: "Vondelpark, Amsterdam",
    Cost: "Free",
    "Student-based": "No",
    image_url: "/placeholder.svg?height=200&width=400",
  },
  {
    Name: "UvA Football Society",
    Sport: "Football, Soccer",
    email: "football@uva.nl",
    website: "https://uva-football.nl",
    Location: "Science Park 904, Amsterdam",
    Cost: "Paid",
    "Student-based": "Yes",
    image_url: "",
  },
  {
    Name: "Yoga in the Park",
    Sport: "Yoga, Meditation",
    email: "namaste@yogapark.nl",
    website: "https://yogapark.nl",
    Location: "Westerpark, Amsterdam",
    Cost: "Paid",
    "Student-based": "No",
    image_url: "/placeholder.svg?height=200&width=400",
  },
  {
    Name: "Student Cycling Group",
    Sport: "Cycling, Mountain biking",
    email: "ride@studentcycling.nl",
    website: "",
    Location: "Various locations, Amsterdam",
    Cost: "Free",
    "Student-based": "Yes",
    image_url: "",
  },
  {
    Name: "Amsterdam Basketball",
    Sport: "Basketball, Streetball",
    email: "hoops@amsterdambasketball.nl",
    website: "https://amsterdambasketball.nl",
    Location: "Sportpark Middenmeer, Amsterdam",
    Cost: "Paid",
    "Student-based": "No",
    image_url: "/placeholder.svg?height=200&width=400",
  },
  {
    Name: "Swimming Club Neptune",
    Sport: "Swimming, Water polo",
    email: "",
    website: "https://neptune-swimming.nl",
    Location: "Zuiderbad, Amsterdam",
    Cost: "NA",
    "Student-based": "No",
    image_url: "",
  },
]

export default function CommunitiesPage() {
  const [communities, setCommunities] = useState(mockCommunities)
  const [searchTerm, setSearchTerm] = useState("")
  const [costFilter, setCostFilter] = useState("all")
  const [studentFilter, setStudentFilter] = useState("all")
  const [sportFilter, setSportFilter] = useState("all")
  const [isMapVisible, setIsMapVisible] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  // Get unique sports for filter
  const uniqueSports = useMemo(() => {
    const sports = new Set()
    communities.forEach((community) => {
      if (community.Sport) {
        community.Sport.split(",").forEach((sport) => {
          sports.add(sport.trim())
        })
      }
    })
    return Array.from(sports).sort()
  }, [communities])

  // Filter communities
  const filteredCommunities = useMemo(() => {
    return communities.filter((community) => {
      const matchesSearch =
        !searchTerm ||
        community.Name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        community.Sport.toLowerCase().includes(searchTerm.toLowerCase()) ||
        community.Location.toLowerCase().includes(searchTerm.toLowerCase())

      const matchesCost =
        costFilter === "all" ||
        (costFilter === "free" && community.Cost === "Free") ||
        (costFilter === "paid" && community.Cost === "Paid") ||
        (costFilter === "na" && community.Cost === "NA")

      const matchesStudent = studentFilter === "all" || community["Student-based"] === studentFilter

      const matchesSport = sportFilter === "all" || community.Sport.toLowerCase().includes(sportFilter.toLowerCase())

      return matchesSearch && matchesCost && matchesStudent && matchesSport
    })
  }, [communities, searchTerm, costFilter, studentFilter, sportFilter])

  const clearFilters = () => {
    setSearchTerm("")
    setCostFilter("all")
    setStudentFilter("all")
    setSportFilter("all")
  }

  const getCostBadgeColor = (cost) => {
    switch (cost) {
      case "Free":
        return "bg-green-100 text-green-700 border-green-200"
      case "Paid":
        return "bg-orange-100 text-orange-700 border-orange-200"
      case "NA":
        return "bg-gray-100 text-gray-700 border-gray-200"
      default:
        return "bg-gray-100 text-gray-700 border-gray-200"
    }
  }

  const getCostDisplayText = (cost) => {
    return cost === "NA" ? "Contact for pricing" : cost
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-orange-50">
      {/* Hero Section */}
      <section className="relative w-full py-12 md:py-24 lg:py-32 overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-orange-900 via-red-900 to-pink-900">
          {/* Floating Elements */}
          <div className="absolute top-20 left-10 w-16 h-16 border-2 border-orange-300/30 rounded-lg rotate-12 animate-pulse"></div>
          <div className="absolute top-40 right-20 w-12 h-12 border-2 border-red-300/30 rounded-full animate-bounce"></div>
          <div className="absolute bottom-32 left-1/4 w-20 h-20 border-2 border-pink-300/30 rounded-lg -rotate-12 animate-pulse"></div>
          <div className="absolute top-1/3 right-1/3 w-8 h-8 bg-orange-400/20 rounded-full animate-ping"></div>
          <div className="absolute bottom-20 right-10 w-14 h-14 border-2 border-red-400/30 rounded-lg rotate-45 animate-pulse"></div>
        </div>

        <div className="relative container mx-auto px-4 md:px-6">
          <div className="flex flex-col items-center text-center space-y-4 mb-8">
            <div className="space-y-2">
              <div className="inline-block rounded-lg bg-orange-100/90 backdrop-blur px-3 py-1 text-sm text-orange-700 font-medium mb-2">
                Community Network
              </div>
              <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-white">
                Find Your Fitness Community
              </h1>
              <p className="max-w-[800px] text-orange-100 md:text-xl">
                Discover the perfect fitness community in Amsterdam that matches your interests, schedule, and goals.
                Connect with like-minded individuals and build lasting exercise habits together.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="relative w-full py-12 md:py-24 bg-gradient-to-b from-slate-50 to-white">
        {/* Subtle Pattern */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(251,146,60,0.05)_1px,transparent_0)] bg-[size:20px_20px]"></div>

        <div className="relative container mx-auto px-4 md:px-6">
          {/* Filters */}
          <div className="mb-8 p-6 bg-gradient-to-r from-orange-50 to-red-50 rounded-xl border border-orange-100/50 shadow-lg backdrop-blur">
            <div className="flex flex-col gap-6">
              {/* Search and Map Toggle Row */}
              <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                <div className="flex-1 space-y-2">
                  <label htmlFor="search" className="text-sm font-medium text-slate-700">
                    Search Communities
                  </label>
                  <div className="relative">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500"
                    >
                      <circle cx="11" cy="11" r="8"></circle>
                      <path d="m21 21-4.3-4.3"></path>
                    </svg>
                    <input
                      id="search"
                      type="text"
                      placeholder="Search by name, sport, or location..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="flex h-10 w-full rounded-md border border-orange-200 bg-white px-3 py-2 text-sm ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 pl-8"
                    />
                  </div>
                </div>

                <button
                  onClick={() => setIsMapVisible(!isMapVisible)}
                  className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-orange-300 bg-white hover:bg-orange-100 hover:text-orange-600 h-10 px-4 py-2 gap-2 text-orange-700"
                >
                  {isMapVisible ? (
                    <>
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="24"
                        height="24"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="h-4 w-4"
                      >
                        <line x1="8" x2="21" y1="6" y2="6"></line>
                        <line x1="8" x2="21" y1="12" y2="12"></line>
                        <line x1="8" x2="21" y1="18" y2="18"></line>
                        <line x1="3" x2="3.01" y1="6" y2="6"></line>
                        <line x1="3" x2="3.01" y1="12" y2="12"></line>
                        <line x1="3" x2="3.01" y1="18" y2="18"></line>
                      </svg>
                      <span>Hide Map</span>
                    </>
                  ) : (
                    <>
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="24"
                        height="24"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="h-4 w-4"
                      >
                        <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon>
                        <line x1="9" x2="9" y1="3" y2="18"></line>
                        <line x1="15" x2="15" y1="6" y2="21"></line>
                      </svg>
                      <span>Show Map</span>
                    </>
                  )}
                </button>
              </div>

              {/* Filter Controls Row */}
              <div className="flex flex-col md:flex-row gap-4 items-start md:items-end">
                <div className="w-full md:w-[180px] space-y-2">
                  <label className="text-sm font-medium text-slate-700">Cost</label>
                  <select
                    value={costFilter}
                    onChange={(e) => setCostFilter(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-orange-200 bg-white px-3 py-2 text-sm ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="all">All Costs</option>
                    <option value="free">Free</option>
                    <option value="paid">Paid</option>
                    <option value="na">Contact for pricing</option>
                  </select>
                </div>

                <div className="w-full md:w-[200px] space-y-2">
                  <label className="text-sm font-medium text-slate-700">Student Focus</label>
                  <select
                    value={studentFilter}
                    onChange={(e) => setStudentFilter(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-orange-200 bg-white px-3 py-2 text-sm ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="all">All Groups</option>
                    <option value="Yes">Student-Based</option>
                    <option value="No">Open to All</option>
                  </select>
                </div>

                <div className="w-full md:w-[180px] space-y-2">
                  <label className="text-sm font-medium text-slate-700">Sport</label>
                  <select
                    value={sportFilter}
                    onChange={(e) => setSportFilter(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-orange-200 bg-white px-3 py-2 text-sm ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="all">All Sports</option>
                    {uniqueSports.map((sport) => (
                      <option key={sport} value={sport}>
                        {sport}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  onClick={clearFilters}
                  className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-orange-300 bg-white hover:bg-orange-100 hover:text-orange-600 h-10 px-4 py-2 gap-2 text-orange-700"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="h-4 w-4"
                  >
                    <path d="m18 6 6 6-6 6"></path>
                    <path d="m6 6 6 6-6 6"></path>
                  </svg>
                  Clear Filters
                </button>
              </div>
            </div>
          </div>

          {/* Results Section */}
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Map Container */}
            {isMapVisible && (
              <div className="lg:w-1/2 bg-white rounded-lg shadow-sm overflow-hidden" style={{ height: "600px" }}>
                <div className="w-full h-full bg-gradient-to-br from-orange-100 to-red-100 flex items-center justify-center">
                  <div className="text-center text-orange-700">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-16 w-16 mx-auto mb-4"
                    >
                      <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon>
                      <line x1="9" x2="9" y1="3" y2="18"></line>
                      <line x1="15" x2="15" y1="6" y2="21"></line>
                    </svg>
                    <p className="text-lg font-semibold">Interactive Map</p>
                    <p className="text-sm">Community locations would appear here</p>
                  </div>
                </div>
              </div>
            )}

            {/* Communities Grid */}
            <div className={`${isMapVisible ? "lg:w-1/2" : "w-full"}`}>
              <div className="mb-6 flex justify-between items-center">
                <h2 className="text-xl font-bold text-slate-800">Communities ({filteredCommunities.length})</h2>
              </div>

              {isLoading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Loading communities...</p>
                </div>
              ) : filteredCommunities.length === 0 ? (
                <div className="text-center py-12">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="h-12 w-12 text-gray-400 mx-auto mb-4"
                  >
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="m21 21-4.3-4.3"></path>
                  </svg>
                  <h3 className="text-xl font-semibold text-gray-700 mb-2">No communities found</h3>
                  <p className="text-gray-600">Try adjusting your filters or search terms</p>
                </div>
              ) : (
                <div className={`grid gap-6 ${isMapVisible ? "grid-cols-1" : "md:grid-cols-2 lg:grid-cols-3"}`}>
                  {filteredCommunities.map((community, index) => (
                    <div
                      key={index}
                      className={`group bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 border border-orange-100 hover:border-orange-300 overflow-hidden ${isMapVisible ? "text-sm" : ""}`}
                    >
                      {/* Image Section */}
                      <div
                        className={`${isMapVisible ? "aspect-[4/3]" : "aspect-video"} bg-gradient-to-br from-orange-100 to-red-100 relative overflow-hidden`}
                      >
                        {community.image_url ? (
                          <img
                            src={community.image_url || "/placeholder.svg"}
                            alt={community.Name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                            onError={(e) => {
                              e.target.style.display = "none"
                              e.target.nextElementSibling.style.display = "flex"
                            }}
                          />
                        ) : null}
                        <div
                          className={`${community.image_url ? "hidden" : "flex"} w-full h-full items-center justify-center`}
                        >
                          <div className="text-center text-orange-700">
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              width="24"
                              height="24"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              className="h-12 w-12 mx-auto mb-2"
                            >
                              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                              <circle cx="9" cy="7" r="4"></circle>
                              <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                            </svg>
                            <p className="text-sm font-medium">{community.Name}</p>
                          </div>
                        </div>
                        <div className="absolute top-2 right-2">
                          <span
                            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border ${getCostBadgeColor(community.Cost)}`}
                          >
                            {getCostDisplayText(community.Cost)}
                          </span>
                        </div>
                      </div>

                      {/* Content Section */}
                      <div className={`${isMapVisible ? "p-4" : "p-6"}`}>
                        <h3
                          className={`${isMapVisible ? "text-base" : "text-lg"} font-semibold text-orange-700 group-hover:text-orange-600 transition-colors mb-3`}
                        >
                          {community.Name}
                        </h3>

                        <div className={`space-y-3 ${isMapVisible ? "mb-3" : "mb-4"}`}>
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <div
                              className={`${isMapVisible ? "w-3 h-3" : "w-4 h-4"} bg-orange-500 rounded-full flex items-center justify-center`}
                            >
                              <span className={`${isMapVisible ? "text-[10px]" : "text-xs"} text-white font-bold`}>
                                S
                              </span>
                            </div>
                            <span>{community.Sport}</span>
                          </div>

                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              width="24"
                              height="24"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              className={`${isMapVisible ? "h-3 w-3" : "h-4 w-4"} text-orange-500`}
                            >
                              <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path>
                              <circle cx="12" cy="10" r="3"></circle>
                            </svg>
                            <span>{community.Location}</span>
                          </div>

                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              width="24"
                              height="24"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              className={`${isMapVisible ? "h-3 w-3" : "h-4 w-4"} text-orange-500`}
                            >
                              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                              <circle cx="9" cy="7" r="4"></circle>
                              <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                            </svg>
                            <span>{community["Student-based"] === "Yes" ? "Student-focused" : "Open to all"}</span>
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-2">
                          {community.website && (
                            <a
                              href={community.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={`flex-1 inline-flex items-center justify-center rounded-lg text-sm font-medium bg-orange-500 hover:bg-orange-600 text-white ${isMapVisible ? "h-8 px-3 py-1" : "h-9 px-4 py-2"} transition-colors`}
                            >
                              <svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="24"
                                height="24"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className="h-4 w-4 mr-1"
                              >
                                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                <polyline points="15 3 21 3 21 9"></polyline>
                                <line x1="10" x2="21" y1="14" y2="3"></line>
                              </svg>
                              Website
                            </a>
                          )}

                          {community.email && (
                            <a
                              href={`mailto:${community.email}`}
                              className={`flex-1 inline-flex items-center justify-center rounded-lg text-sm font-medium border border-orange-300 bg-white hover:bg-orange-50 text-orange-700 ${isMapVisible ? "h-8 px-3 py-1" : "h-9 px-4 py-2"} transition-colors`}
                            >
                              <svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="24"
                                height="24"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className="h-4 w-4 mr-1"
                              >
                                <rect width="20" height="16" x="2" y="4" rx="2"></rect>
                                <path d="m22 7-10 5L2 7"></path>
                              </svg>
                              Contact
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Add Community Section */}
      <section className="w-full py-16 bg-gradient-to-br from-orange-900 via-red-900 to-pink-900">
        <div className="container mx-auto px-4 md:px-6 max-w-2xl">
          <div className="bg-white/10 backdrop-blur rounded-xl shadow-lg p-8 border border-orange-300/30">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold mb-4 text-white">Add Your Community</h2>
              <p className="text-orange-100">
                Help us grow our community directory by adding your sports group or club.
              </p>
            </div>

            <div className="text-center">
              <button className="inline-flex items-center justify-center rounded-full text-lg font-semibold bg-orange-500 hover:bg-orange-600 text-white h-12 px-8 py-3 transition-colors">
                Submit Community
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
