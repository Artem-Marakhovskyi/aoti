
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
   maxT = 24
   noSym = 24
   start = [
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0, 74, 57,  0,  0, 58,  1,  0,  0,
    59, 59, 59, 59, 59, 59, 59, 59, 59, 59,  0,  0, 20,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  7,
     0, 22, 44, 69, 68, 49, 12,  0,  0, 39,  0,  0,  0, 67, 65, 17,
    32,  0,  0,  0,  9,  0,  0,  0,  0,  0,  0, 75,  0, 76,  0,  0,
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
            if self.ch == 'e':
               buf += unicode(self.ch)
               self.NextCh()
               state = 2
            elif self.ch == 'l':
               buf += unicode(self.ch)
               self.NextCh()
               state = 3
            elif self.ch == 'g':
               buf += unicode(self.ch)
               self.NextCh()
               state = 4
            elif self.ch == 'n':
               buf += unicode(self.ch)
               self.NextCh()
               state = 5
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 2:
            if self.ch == 'q':
               buf += unicode(self.ch)
               self.NextCh()
               state = 6
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 3:
            if self.ch == 'e':
               buf += unicode(self.ch)
               self.NextCh()
               state = 6
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 4:
            if self.ch == 'e':
               buf += unicode(self.ch)
               self.NextCh()
               state = 6
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 5:
            if self.ch == 'e':
               buf += unicode(self.ch)
               self.NextCh()
               state = 6
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 6:
            self.t.kind = 1
            done = True
         elif state == 7:
            if (self.ch >= 'a' and self.ch <= 'z'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 8
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 8:
            if (self.ch >= '0' and self.ch <= '9'
                 or self.ch >= 'a' and self.ch <= 'z'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 8
            else:
               self.t.kind = 2
               done = True
         elif state == 9:
            if self.ch == 'r':
               buf += unicode(self.ch)
               self.NextCh()
               state = 10
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 10:
            if self.ch == 'u':
               buf += unicode(self.ch)
               self.NextCh()
               state = 11
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 11:
            if self.ch == 'e':
               buf += unicode(self.ch)
               self.NextCh()
               state = 16
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 12:
            if self.ch == 'a':
               buf += unicode(self.ch)
               self.NextCh()
               state = 13
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 13:
            if self.ch == 'l':
               buf += unicode(self.ch)
               self.NextCh()
               state = 14
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 14:
            if self.ch == 's':
               buf += unicode(self.ch)
               self.NextCh()
               state = 15
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 15:
            if self.ch == 'e':
               buf += unicode(self.ch)
               self.NextCh()
               state = 16
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 16:
            self.t.kind = 3
            done = True
         elif state == 17:
            if self.ch == 'u':
               buf += unicode(self.ch)
               self.NextCh()
               state = 18
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 18:
            if self.ch == 't':
               buf += unicode(self.ch)
               self.NextCh()
               state = 19
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 19:
            self.t.kind = 4
            done = True
         elif state == 20:
            if self.ch == '-':
               buf += unicode(self.ch)
               self.NextCh()
               state = 21
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 21:
            self.t.kind = 5
            done = True
         elif state == 22:
            if self.ch == 's':
               buf += unicode(self.ch)
               self.NextCh()
               state = 23
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 23:
            if self.ch == 's':
               buf += unicode(self.ch)
               self.NextCh()
               state = 24
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 24:
            if self.ch == 'i':
               buf += unicode(self.ch)
               self.NextCh()
               state = 25
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 25:
            if self.ch == 'g':
               buf += unicode(self.ch)
               self.NextCh()
               state = 26
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 26:
            if self.ch == 'n':
               buf += unicode(self.ch)
               self.NextCh()
               state = 27
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 27:
            self.t.kind = 6
            done = True
         elif state == 28:
            if self.ch == 'l':
               buf += unicode(self.ch)
               self.NextCh()
               state = 29
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 29:
            self.t.kind = 7
            done = True
         elif state == 30:
            if self.ch == 'v':
               buf += unicode(self.ch)
               self.NextCh()
               state = 31
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 31:
            self.t.kind = 8
            done = True
         elif state == 32:
            if self.ch == 'l':
               buf += unicode(self.ch)
               self.NextCh()
               state = 33
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 33:
            if self.ch == 'u':
               buf += unicode(self.ch)
               self.NextCh()
               state = 34
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 34:
            self.t.kind = 9
            done = True
         elif state == 35:
            if self.ch == 'n':
               buf += unicode(self.ch)
               self.NextCh()
               state = 36
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 36:
            if self.ch == 'u':
               buf += unicode(self.ch)
               self.NextCh()
               state = 37
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 37:
            if self.ch == 's':
               buf += unicode(self.ch)
               self.NextCh()
               state = 38
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 38:
            self.t.kind = 10
            done = True
         elif state == 39:
            if self.ch == 'n':
               buf += unicode(self.ch)
               self.NextCh()
               state = 40
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 40:
            if self.ch == 'c':
               buf += unicode(self.ch)
               self.NextCh()
               state = 41
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 41:
            self.t.kind = 11
            done = True
         elif state == 42:
            if self.ch == 'c':
               buf += unicode(self.ch)
               self.NextCh()
               state = 43
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 43:
            self.t.kind = 12
            done = True
         elif state == 44:
            if self.ch == 'e':
               buf += unicode(self.ch)
               self.NextCh()
               state = 45
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 45:
            if self.ch == 'g':
               buf += unicode(self.ch)
               self.NextCh()
               state = 46
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 46:
            if self.ch == 'i':
               buf += unicode(self.ch)
               self.NextCh()
               state = 47
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 47:
            if self.ch == 'n':
               buf += unicode(self.ch)
               self.NextCh()
               state = 48
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 48:
            self.t.kind = 13
            done = True
         elif state == 49:
            if self.ch == 'n':
               buf += unicode(self.ch)
               self.NextCh()
               state = 50
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 50:
            if self.ch == 'd':
               buf += unicode(self.ch)
               self.NextCh()
               state = 51
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 51:
            self.t.kind = 14
            done = True
         elif state == 52:
            if self.ch == 'n':
               buf += unicode(self.ch)
               self.NextCh()
               state = 53
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 53:
            if self.ch == 'd':
               buf += unicode(self.ch)
               self.NextCh()
               state = 54
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 54:
            self.t.kind = 15
            done = True
         elif state == 55:
            if self.ch == '(':
               buf += unicode(self.ch)
               self.NextCh()
               state = 56
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 56:
            self.t.kind = 16
            done = True
         elif state == 57:
            self.t.kind = 17
            done = True
         elif state == 58:
            self.t.kind = 18
            done = True
         elif state == 59:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 59
            elif self.ch == '.':
               buf += unicode(self.ch)
               self.NextCh()
               state = 60
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 60:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 61
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 61:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 61
            elif self.ch == 'e':
               buf += unicode(self.ch)
               self.NextCh()
               state = 62
            else:
               self.t.kind = 19
               done = True
         elif state == 62:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 64
            elif (self.ch == '+'
                 or self.ch == '-'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 63
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 63:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 64
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 64:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 64
            else:
               self.t.kind = 19
               done = True
         elif state == 65:
            if self.ch == 'l':
               buf += unicode(self.ch)
               self.NextCh()
               state = 66
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 66:
            self.t.kind = 20
            done = True
         elif state == 67:
            if self.ch == 'u':
               buf += unicode(self.ch)
               self.NextCh()
               state = 28
            elif self.ch == 'i':
               buf += unicode(self.ch)
               self.NextCh()
               state = 35
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 68:
            if self.ch == 'i':
               buf += unicode(self.ch)
               self.NextCh()
               state = 30
            elif self.ch == 'e':
               buf += unicode(self.ch)
               self.NextCh()
               state = 42
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 69:
            if self.ch == 'o':
               buf += unicode(self.ch)
               self.NextCh()
               state = 52
            elif self.ch == 'y':
               buf += unicode(self.ch)
               self.NextCh()
               state = 70
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 70:
            if self.ch == 'c':
               buf += unicode(self.ch)
               self.NextCh()
               state = 71
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 71:
            if self.ch == 'l':
               buf += unicode(self.ch)
               self.NextCh()
               state = 72
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 72:
            if self.ch == 'e':
               buf += unicode(self.ch)
               self.NextCh()
               state = 73
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 73:
            if (self.ch == ' '):
               buf += unicode(self.ch)
               self.NextCh()
               state = 55
            elif self.ch == '(':
               buf += unicode(self.ch)
               self.NextCh()
               state = 56
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 74:
            self.t.kind = 21
            done = True
         elif state == 75:
            self.t.kind = 22
            done = True
         elif state == 76:
            self.t.kind = 23
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

