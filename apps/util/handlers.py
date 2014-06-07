# Copyright (C) 2014 Taylor Turpen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

class WerHandler(object):
    MAXIMUM_WRONG_CHARACTERS = 2
    MINMUM_CHARACTERS_FOR_CER = 5
    
    def wer(self,ref,hyp):
        d = []
        #zeros
        for j in range(len(ref)+1):
            d.append([0.0]*(len(hyp)+1))
        #initialize
        for i in range(len(d)):
            for j in range(len(d[0])):
                if i == 0:
                    d[0][j] = j
                elif j == 0:
                    d[i][0] = i
        #calculate            
        for i in range(1, len(d)):
            for j in range(1, len(d[0])):
                if ref[i-1].lower() == hyp[j-1].lower():
                    d[i][j] = d[i-1][j-1]
                else:
                    sub = d[i-1][j-1] + 1
                    ins = d[i][j-1] + 1
                    deletion = d[i-1][j] + 1
                    d[i][j] = min(sub,ins,deletion)
        return float(d[len(ref)][len(hyp)])/float(len(ref))
    
    def cer_wer(self,ref,hyp,min_char_df=MAXIMUM_WRONG_CHARACTERS):
        d = []
        #zeros
        for j in range(len(ref)+1):
            d.append([0]*(len(hyp)+1))
        #initialize
        for i in range(len(d)):
            for j in range(len(d[0])):
                if i == 0:
                    d[0][j] = j
                elif j == 0:
                    d[i][0] = i
        #calculate            
        for i in range(1, len(d)):
            for j in range(1, len(d[0])):
                if self.cer_compare(ref[i-1].lower(),hyp[j-1].lower(),min_char_df=min_char_df):
                    d[i][j] = d[i-1][j-1]
                else:
                    sub = d[i-1][j-1] + 1
                    ins = d[i][j-1] + 1
                    deletion = d[i-1][j] + 1
                    d[i][j] = min(sub,ins,deletion)
        return float(d[len(ref)][len(hyp)])/float(len(ref))
    
    def cer_compare(self,ref_tok,hyp_tok,min_char_df=MAXIMUM_WRONG_CHARACTERS):
        """If the reference token has the minimum number of characters
            and the character error rate is below the threshold
            return True
            else return False or their comparison"""
        cer = self.wer(ref_tok,hyp_tok)
        if len(ref_tok) >= self.MINMUM_CHARACTERS_FOR_CER:
            if cer <= min_char_df/len(ref_tok):
                return True
            return False
        return ref_tok == hyp_tok
