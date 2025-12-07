import SwiftUI

struct AppIconView: View {
    let item: AppItem
    let size: CGFloat
    let isSelected: Bool
    
    @StateObject private var iconManager = IconManager.shared
    
    var body: some View {
        VStack(spacing: 4) {
            iconManager.image(for: item)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: size, height: size)
                .shadow(radius: isSelected ? 5 : 0)
                .scaleEffect(isSelected ? 1.1 : 1.0)
                .animation(.spring(response: 0.3, dampingFraction: 0.6), value: isSelected)
            
            Text(item.name)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.white)
                .lineLimit(1)
                .shadow(color: .black.opacity(0.5), radius: 2, x: 0, y: 1)
        }
        .frame(width: size + 20) // Hit area padding
        .padding(8)
        .contentShape(Rectangle())
    }
}
