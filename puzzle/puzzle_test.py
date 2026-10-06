from load_puzzles import Puzzles

puzzles = Puzzles(10000)

puzzles.retrieve_puzzle(800,800,"rookEndgame")


#puzzles = load_puzzles(10000)
# puzzles_by_rating = load_puzzles_by_rating(10000) # rating 300 to 3000

# for rating, puzzles in puzzles_by_rating.items():
#     print(f"rating: {rating}, n_puzzles: {len(puzzles)}")
#for p in puzzles:


#print(len(puzzles))

# short: 50246
# endgame: 50229
# middlegame: 44960
# crushing: 38379
# mate: 31882
# advantage: 28670
# long: 25980
# oneMove: 14888
# mateIn1: 14854
# master: 13702
# mateIn2: 13245
# fork: 12818
# kingsideAttack: 8698
# veryLong: 8020
# sacrifice: 7599
# advancedPawn: 6171
# defensiveMove: 6030
# pin: 5998
# rookEndgame: 5442
# discoveredAttack: 5104
# opening: 4811
# deflection: 4311
# quietMove: 4138
# pawnEndgame: 3640
# attraction: 3616
# hangingPiece: 3560
# backRankMate: 3381
# mateIn3: 3215
# exposedKing: 2944
# promotion: 2366
# skewer: 2203
# discoveredCheck: 1797
# queensideAttack: 1545
# bishopEndgame: 1360
# clearance: 1360
# masterVsMaster: 1239
# queenEndgame: 1198
# intermezzo: 1147
# trappedPiece: 1092
# operaMate: 1079
# zugzwang: 1038
# pillsburysMate: 1034
# knightEndgame: 818
# queenRookEndgame: 786
# attackingF2F7: 758
# capturingDefender: 612
# doubleCheck: 516
# mateIn4: 488
# smotheredMate: 400
# epauletteMate: 378
# interference: 349
# xRayAttack: 320
# equality: 203
# cornerMate: 191
# hookMate: 165
# swallowstailMate: 147
# enPassant: 142
# anastasiaMate: 131
# triangleMate: 125
# arabianMate: 121
# collinearMove: 111
# morphysMate: 108
# killBoxMate: 89
# blindSwineMate: 86
# mateIn5: 80