def over_under_live(pts, half, time):
    if half == 1:
        proj = (pts / (20 - time)) * 40
    print proj
    return proj

if __name__ == "__main__":
    over_under_live()
