import org.apache.calcite.avatica.util.Casing;
import org.apache.calcite.avatica.util.Quoting;
import org.apache.calcite.sql.SqlNode;
import org.apache.calcite.sql.parser.SqlParseException;
import org.apache.calcite.sql.parser.impl.SqlParserImpl;
import org.apache.calcite.sql.validate.SqlConformanceEnum;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;


public class SQLParser {
    static private String treeToJson(SqlNode sqlNode) {
        Gson gson = new GsonBuilder().create();
        return gson.toJson(sqlNode);
    }
    public static void main(String[] args) {
        if(args.length < 1) {
            System.err.println("Please Input a SQL");
            return;
        }
        String sql4 = args[0];
        org.apache.calcite.sql.parser.SqlParser sqlParser = org.apache.calcite.sql.parser.SqlParser.create(sql4,
                org.apache.calcite.sql.parser.SqlParser.configBuilder()
                        .setParserFactory(SqlParserImpl.FACTORY)
                        .setQuoting(Quoting.DOUBLE_QUOTE)
                        .setUnquotedCasing(Casing.UNCHANGED)
                        .setQuotedCasing(Casing.UNCHANGED)
                        .setConformance(SqlConformanceEnum.DEFAULT)
                        .build());
        try {
            SqlNode sqlNode = sqlParser.parseStmt();
            System.out.println(SQLParser.treeToJson(sqlNode));
        } catch (SqlParseException e) {
            e.printStackTrace();
        }
    }
}
