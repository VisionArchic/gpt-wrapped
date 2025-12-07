import SwiftUI
import Combine

class LauncherViewModel: ObservableObject {
    @Published var searchText: String = ""
    @Published var currentPageIndex: Int = 0
    @Published var selectedAppID: String? // For keyboard navigation
    
    // Raw data
    @Published private(set) var allApps: [AppItem] = []
    
    // Display data
    @Published var pages: [[AppItem]] = [] // Simple array of pages for now (auto-flow)
    @Published var filteredApps: [AppItem] = []
    
    private var scanner = AppScanner()
    private var cancellables = Set<AnyCancellable>()
    
    var isSearching: Bool { !searchText.isEmpty }
    
    init() {
        // Bind to scanner
        scanner.$apps
            .receive(on: RunLoop.main)
            .sink { [weak self] apps in
                self?.allApps = apps
                self?.reflowPages(rows: 4, cols: 7) // Default defaults, will bind to settings later
            }
            .store(in: &cancellables)
        
        // Scan on init
        scanner.scan()
    }
    
    func reflowPages(rows: Int, cols: Int) {
        guard !isSearching else { return }
        // Simple auto-flow logic for MVP. 
        // Later we will respect Persisted Layout.
        
        let pageSize = rows * cols
        if pageSize == 0 { return }
        
        pages = allApps.chunked(into: pageSize)
    }
    
    func filterApps() {
        if searchText.isEmpty {
            filteredApps = []
        } else {
            filteredApps = allApps.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
        }
    }
    
    // MARK: - Navigation
    
    enum Direction {
        case up, down, left, right
    }
    
    func navigateSelection(_ direction: Direction, cols: Int) {
        // If nothing selected, select first item
        guard let currentID = selectedAppID else {
            selectedAppID = pages.first?.first?.bundleIdentifier
            return
        }
        
        // Find current position
        // Determine if we are in search results or paged mode
        let currentList = isSearching ? filteredApps : (pages.indices.contains(currentPageIndex) ? pages[currentPageIndex] : [])
        
        guard let index = currentList.firstIndex(where: { $0.bundleIdentifier == currentID }) else {
            selectedAppID = currentList.first?.bundleIdentifier
            return
        }
        
        var newIndex = index
        
        switch direction {
        case .left:
            newIndex = max(0, index - 1)
            // Handle page navigation if at start? 
            // For now, strict bounds.
        case .right:
            newIndex = min(currentList.count - 1, index + 1)
        case .up:
            newIndex = max(0, index - cols)
        case .down:
            newIndex = min(currentList.count - 1, index + cols)
        }
        
        if newIndex != index {
            selectedAppID = currentList[newIndex].bundleIdentifier
        }
    }
    
    func launchSelected() {
        guard let id = selectedAppID,
              let app = allApps.first(where: { $0.bundleIdentifier == id }) else { return }
        
        NSWorkspace.shared.open(URL(fileURLWithPath: app.path))
        NSApplication.shared.hide(nil)
    }
}

// Helper for chunking
extension Array {
    func chunked(into size: Int) -> [[Element]] {
        return stride(from: 0, to: count, by: size).map {
            Array(self[$0 ..< Swift.min($0 + size, count)])
        }
    }
}
