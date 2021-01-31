
import sys

class Token( object ):
   def __init__( self ):
      self.kind   = 0     # token kind
      self.pos    = 0     # token position in the source text (starting at 0)
      self.col    = 0     # token column (starting at 0)
      self.line   = 0     # token line (starting at 1)
      self.val    = u''   # token value
      self.next   = None  # AW 2003-03-07 Tokens are kept in linked list


class Position( object ):    # position of source code stretch (e.g. semantic action, resolver expressions)
   def __init__( self, buf, beg, len, col ):
      assert isinstance( buf, Buffer )
      assert isinstance( beg, int )
      assert isinstance( len, int )
      assert isinstance( col, int )

      self.buf = buf
      self.beg = beg   # start relative to the beginning of the file
      self.len = len   # length of stretch
      self.col = col   # column number of start position

   def getSubstring( self ):
      return self.buf.readPosition( self )

class Buffer( object ):
   EOF      = u'\u0100'     # 256

   def __init__( self, s ):
      self.buf    = s
      self.bufLen = len(s)
      self.pos    = 0
      self.lines  = s.splitlines( True )

   def Read( self ):
      if self.pos < self.bufLen:
         result = self.buf[self.pos]
         self.pos += 1
         return result
      else:
         return Buffer.EOF

   def ReadChars( self, numBytes=1 ):
      result = self.buf[ self.pos : self.pos + numBytes ]
      self.pos += numBytes
      return result

   def Peek( self ):
      if self.pos < self.bufLen:
         return self.buf[self.pos]
      else:
         return Scanner.buffer.EOF

   def getString( self, beg, end ):
      s = ''
      oldPos = self.getPos( )
      self.setPos( beg )
      while beg < end:
         s += self.Read( )
         beg += 1
      self.setPos( oldPos )
      return s

   def getPos( self ):
      return self.pos

   def setPos( self, value ):
      if value < 0:
         self.pos = 0
      elif value >= self.bufLen:
         self.pos = self.bufLen
      else:
         self.pos = value

   def readPosition( self, pos ):
      assert isinstance( pos, Position )
      self.setPos( pos.beg )
      return self.ReadChars( pos.len )

   def __iter__( self ):
      return iter(self.lines)

class Scanner(object):
   EOL     = u'\n'
   eofSym  = 0

   charSetSize = 256
   maxT = 20
   noSym = 20
   start = [
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0, 19,  6,  0,  0,  7,  0,  0,  0,
     8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  0,  0,  2,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  1,  1, 14,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     -1]
   valCh = u''       # current input character (for token.val)

   def __init__( self, s ):
      self.buffer = Buffer( unicode(s) ) # the buffer instance

      self.ch        = u'\0'       # current input character
      self.pos       = -1          # column number of current character
      self.line      = 1           # line number of current character
      self.lineStart = 0           # start position of current line
      self.oldEols   = 0           # EOLs that appeared in a comment;
      self.NextCh( )
      self.ignore    = set( )      # set of characters to be ignored by the scanner
      self.ignore.add( ord(' ') )  # blanks are always white space
      self.ignore.add(9) 
      self.ignore.add(10) 
      self.ignore.add(13) 

      # fill token list
      self.tokens = Token( )       # the complete input token stream
      node   = self.tokens

      node.next = self.NextToken( )
      node = node.next
      while node.kind != Scanner.eofSym:
         node.next = self.NextToken( )
         node = node.next

      node.next = node
      node.val  = u'EOF'
      self.t  = self.tokens     # current token
      self.pt = self.tokens     # current peek token

   def NextCh( self ):
      if self.oldEols > 0:
         self.ch = Scanner.EOL
         self.oldEols -= 1
      else:
         self.ch = self.buffer.Read( )
         self.pos += 1
         # replace isolated '\r' by '\n' in order to make
         # eol handling uniform across Windows, Unix and Mac
         if (self.ch == u'\r') and (self.buffer.Peek() != u'\n'):
            self.ch = Scanner.EOL
         if self.ch == Scanner.EOL:
            self.line += 1
            self.lineStart = self.pos + 1
            valCh = self.ch
      if self.ch != Buffer.EOF:
         self.ch = self.ch.lower()




   def Comment0( self ):
      level = 1
      line0 = self.line
      lineStart0 = self.lineStart
      self.NextCh()
      if self.ch == '*':
         self.NextCh()
         while True:
            if self.ch == '*':
               self.NextCh()
               if self.ch == '/':
                  level -= 1
                  if level == 0:
                     self.oldEols = self.line - line0
                     self.NextCh()
                     return True
                  self.NextCh()
            elif self.ch == Buffer.EOF:
               return False
            else:
               self.NextCh()
      else:
         if self.ch == Scanner.EOL:
            self.line -= 1
            self.lineStart = lineStart0
         self.pos = self.pos - 2
         self.buffer.setPos(self.pos+1)
         self.NextCh()
      return False

   def Comment1( self ):
      level = 1
      line0 = self.line
      lineStart0 = self.lineStart
      self.NextCh()
      if self.ch == '-':
         self.NextCh()
         while True:
            if ord(self.ch) == 10:
               level -= 1
               if level == 0:
                  self.oldEols = self.line - line0
                  self.NextCh()
                  return True
               self.NextCh()
            elif self.ch == Buffer.EOF:
               return False
            else:
               self.NextCh()
      else:
         if self.ch == Scanner.EOL:
            self.line -= 1
            self.lineStart = lineStart0
         self.pos = self.pos - 2
         self.buffer.setPos(self.pos+1)
         self.NextCh()
      return False


   def CheckLiteral( self ):
      lit = self.t.val.lower()
      if lit == "out":
         self.t.kind = 2
      elif lit == "assign":
         self.t.kind = 4
      elif lit == "mul":
         self.t.kind = 5
      elif lit == "div":
         self.t.kind = 6
      elif lit == "plu":
         self.t.kind = 7
      elif lit == "minus":
         self.t.kind = 8
      elif lit == "inc":
         self.t.kind = 9
      elif lit == "dec":
         self.t.kind = 10
      elif lit == "begin":
         self.t.kind = 11
      elif lit == "end":
         self.t.kind = 12
      elif lit == "cond":
         self.t.kind = 13
      elif lit == "nl":
         self.t.kind = 18


   def NextToken( self ):
      while ord(self.ch) in self.ignore:
         self.NextCh( )
      if (self.ch == '/' and self.Comment0() or self.ch == '-' and self.Comment1()):
         return self.NextToken()

      self.t = Token( )
      self.t.pos = self.pos
      self.t.col = self.pos - self.lineStart + 1
      self.t.line = self.line
      if ord(self.ch) < len(self.start):
         state = self.start[ord(self.ch)]
      else:
         state = 0
      buf = u''
      buf += unicode(self.ch)
      self.NextCh()

      done = False
      while not done:
         if state == -1:
            self.t.kind = Scanner.eofSym     # NextCh already done
            done = True
         elif state == 0:
            self.t.kind = Scanner.noSym      # NextCh already done
            done = True
         elif state == 1:
            if (self.ch >= '0' and self.ch <= '9'
                 or self.ch >= 'a' and self.ch <= 'z'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 1
            else:
               self.t.kind = 1
               self.t.val = buf
               self.CheckLiteral()
               return self.t
         elif state == 2:
            if self.ch == '-':
               buf += unicode(self.ch)
               self.NextCh()
               state = 3
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 3:
            self.t.kind = 3
            done = True
         elif state == 4:
            if self.ch == '(':
               buf += unicode(self.ch)
               self.NextCh()
               state = 5
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 5:
            self.t.kind = 14
            done = True
         elif state == 6:
            self.t.kind = 15
            done = True
         elif state == 7:
            self.t.kind = 16
            done = True
         elif state == 8:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 8
            elif self.ch == '.':
               buf += unicode(self.ch)
               self.NextCh()
               state = 9
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 9:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 10
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 10:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 10
            elif self.ch == 'e':
               buf += unicode(self.ch)
               self.NextCh()
               state = 11
            else:
               self.t.kind = 17
               done = True
         elif state == 11:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 13
            elif (self.ch == '+'
                 or self.ch == '-'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 12
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 12:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 13
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 13:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 13
            else:
               self.t.kind = 17
               done = True
         elif state == 14:
            if (self.ch >= '0' and self.ch <= '9'
                 or self.ch >= 'a' and self.ch <= 'x'
                 or self.ch == 'z'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 1
            elif self.ch == 'y':
               buf += unicode(self.ch)
               self.NextCh()
               state = 15
            else:
               self.t.kind = 1
               self.t.val = buf
               self.CheckLiteral()
               return self.t
         elif state == 15:
            if (self.ch >= '0' and self.ch <= '9'
                 or self.ch >= 'a' and self.ch <= 'b'
                 or self.ch >= 'd' and self.ch <= 'z'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 1
            elif self.ch == 'c':
               buf += unicode(self.ch)
               self.NextCh()
               state = 16
            else:
               self.t.kind = 1
               self.t.val = buf
               self.CheckLiteral()
               return self.t
         elif state == 16:
            if (self.ch >= '0' and self.ch <= '9'
                 or self.ch >= 'a' and self.ch <= 'k'
                 or self.ch >= 'm' and self.ch <= 'z'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 1
            elif self.ch == 'l':
               buf += unicode(self.ch)
               self.NextCh()
               state = 17
            else:
               self.t.kind = 1
               self.t.val = buf
               self.CheckLiteral()
               return self.t
         elif state == 17:
            if (self.ch >= '0' and self.ch <= '9'
                 or self.ch >= 'a' and self.ch <= 'd'
                 or self.ch >= 'f' and self.ch <= 'z'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 1
            elif self.ch == 'e':
               buf += unicode(self.ch)
               self.NextCh()
               state = 18
            else:
               self.t.kind = 1
               self.t.val = buf
               self.CheckLiteral()
               return self.t
         elif state == 18:
            if (self.ch >= '0' and self.ch <= '9'
                 or self.ch >= 'a' and self.ch <= 'z'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 1
            elif (self.ch == ' '):
               buf += unicode(self.ch)
               self.NextCh()
               state = 4
            elif self.ch == '(':
               buf += unicode(self.ch)
               self.NextCh()
               state = 5
            else:
               self.t.kind = 1
               self.t.val = buf
               self.CheckLiteral()
               return self.t
         elif state == 19:
            self.t.kind = 19
            done = True

      self.t.val = buf
      return self.t

   def Scan( self ):
      self.t = self.t.next
      self.pt = self.t.next
      return self.t

   def Peek( self ):
      self.pt = self.pt.next
      while self.pt.kind > self.maxT:
         self.pt = self.pt.next

      return self.pt

   def ResetPeek( self ):
      self.pt = self.t

