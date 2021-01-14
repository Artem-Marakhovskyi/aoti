# Поместить '$', затем S в магазин;
# do
# 	{X=верхний символ магазина;
# if (X - терминал)
# 	if (X==InSym)
# 		{удалить X из магазина;
# 		InSym=очередной символ;
# 		}
# 	else {error(); break;}
# else if (X - нетерминал)
# 	if (M[X,InSym]=="X->Y1Y2...Yk")
# 	 {удалить X из магазина;
# 	  поместить Yk,Yk-1,...Y1 в магазин
# 		(Y1 на верхушку);
# 	  вывести правило X->Y1Y2...Yk;
# 	 }
# 	else {error(); break;} /*вход таблицы M пуст*/
#  }
# while (X!='$'); /*магазин пуст*/
# if (InSym != '$') error(); /*Не вся строка прочитана*/

class SymbolStack:
    def __init__(self):
        self.storage = []

    def push(self, obj):
        self.storage.append(obj)

    def pop(self):
        return self.storage.pop(-1)

    def peek(self):
        return self.storage[-1]

class SyntaxAnalyzer:
    def __init__(self):
        self.stack = SymbolStack()
        self.ruleTable =

    def analyze(self, input):
        self.input = input
